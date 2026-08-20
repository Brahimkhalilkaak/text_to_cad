"""LangGraph agent: CAD Implementation Engineer.

Input : a JSON CAD spec (source of truth - the agent never sees how it was made).
Output: generated_part.py (build123d script) + generated_part.stl.

Flow: read spec -> LLM generates build123d code -> execute & verify.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

import config

PROMPTS_DIR = Path(__file__).parent / "prompts"
PROMPT_FILE = PROMPTS_DIR / "cad_coder.md"
OUT_DIR = Path(__file__).parent / "out"
INTERMEDIATE_DIR = OUT_DIR / "intermediate"
OUT_FILE = INTERMEDIATE_DIR / "generated_part.py"
STL_FILE = OUT_DIR / "generated_part.stl"
EXEC_TIMEOUT_S = 120

_CODE_BLOCK_RE = re.compile(r"```(?:python|py)?\s*(.*?)```", re.DOTALL)


class CoderState(TypedDict, total=False):
    spec: Dict[str, Any]
    code: str
    error: str
    spec_path: str


def _build_llm() -> ChatOpenAI:
    if not config.API_KEY:
        raise RuntimeError(
            "OpenCode API key is missing. Set OPENCODE_API_KEY in config.py "
            "or as an environment variable."
        )
    return ChatOpenAI(
        model=config.MODEL,
        api_key=config.API_KEY,
        base_url=config.BASE_URL,
        temperature=config.TEMPERATURE,
    )


def _load_prompt() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE}")
    return PROMPT_FILE.read_text(encoding="utf-8")


def _extract_code(text: str) -> str:
    match = _CODE_BLOCK_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def read_spec(state: CoderState) -> CoderState:
    spec_path = Path(state.get("spec_path") or (INTERMEDIATE_DIR / "spec.json"))
    if not spec_path.exists():
        return {"error": f"Spec file not found: {spec_path}"}
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    return {"spec": spec}


def generate_code(state: CoderState) -> CoderState:
    llm = _build_llm()
    system = SystemMessage(content=_load_prompt())
    spec_text = json.dumps(state["spec"], indent=2, ensure_ascii=False)
    human = HumanMessage(content=f"Build the part described by this spec:\n{spec_text}")

    response = llm.invoke([system, human])
    code = _extract_code(str(response.content))
    if not code:
        return {"error": "LLM returned empty output."}
    return {"code": code}


def execute_code(state: CoderState) -> CoderState:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(state["code"], encoding="utf-8")
    try:
        proc = subprocess.run(
            [sys.executable, str(OUT_FILE)],
            cwd=OUT_DIR,
            capture_output=True,
            text=True,
            timeout=EXEC_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        return {"error": f"Script timed out after {EXEC_TIMEOUT_S}s."}

    if proc.returncode != 0:
        return {
            "error": f"Script exited with code {proc.returncode}: "
            f"{(proc.stderr or proc.stdout or '').strip()[-2000:]}"
        }

    if not STL_FILE.exists():
        return {"error": "Script ran but did not produce generated_part.stl."}

    return {}


def error_node(state: CoderState) -> CoderState:
    print(f"[cad_coder error] {state.get('error', 'unknown error')}")
    return {}


def build_graph():
    builder = StateGraph(CoderState)
    builder.add_node("read_spec", read_spec)
    builder.add_node("generate_code", generate_code)
    builder.add_node("execute_code", execute_code)
    builder.add_node("error", error_node)

    builder.add_edge(START, "read_spec")
    builder.add_conditional_edges(
        "read_spec",
        lambda s: "error" if s.get("error") else "generate_code",
        {"generate_code": "generate_code", "error": "error"},
    )
    builder.add_edge("generate_code", "execute_code")
    builder.add_conditional_edges(
        "execute_code",
        lambda s: "error" if s.get("error") else END,
        {"error": "error", END: END},
    )
    builder.add_edge("error", END)

    return builder.compile()


def generate(spec: Dict[str, Any]) -> Path:
    spec_path = INTERMEDIATE_DIR / "spec.json"
    spec_path.parent.mkdir(parents=True, exist_ok=True)
    spec_path.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    graph = build_graph()
    result = graph.invoke({})
    if result.get("error"):
        raise RuntimeError(result["error"])
    return OUT_FILE


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print('usage: python cad_coder.py "<path to spec.json>"', file=sys.stderr)
        return 1
    spec_path = args[0]

    try:
        spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[cad_coder error] could not read spec: {exc}", file=sys.stderr)
        return 1

    try:
        generate(spec)
    except Exception as exc:  # noqa: BLE001
        print(f"[cad_coder error] {exc}", file=sys.stderr)
        return 1

    print(f"[written] {OUT_FILE}")
    print(f"[written] {STL_FILE}" if STL_FILE.exists() else "[missing] STL not produced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())