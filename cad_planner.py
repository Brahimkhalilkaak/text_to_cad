"""LangGraph agent: Lead System Engineer for mechanical CAD spec planning.

Pipeline:  plain text -> extract/plan (LLM) -> validate/default (rules)
           -> write JSON spec file.
"""

import json
from pathlib import Path
from typing import Any, Dict, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

import config
from spec_schema import CadSpec

PROMPTS_DIR = Path(__file__).parent / "prompts"
PROMPT_FILE = PROMPTS_DIR / "cad_spec_planner.md"


class AgentState(TypedDict, total=False):
    input_text: str
    spec: Dict[str, Any]
    error: str


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
    ).with_structured_output(CadSpec, method="json_mode", include_raw=True)


def _load_prompt() -> str:
    if not PROMPT_FILE.exists():
        raise FileNotFoundError(f"Prompt file not found: {PROMPT_FILE}")
    instructions = PROMPT_FILE.read_text(encoding="utf-8")
    schema = json.dumps(CadSpec.model_json_schema(), indent=2, ensure_ascii=False)
    return f"{instructions}\n\n# JSON SCHEMA (output MUST match this shape)\n{schema}"


def _coerce(spec: CadSpec) -> CadSpec:
    """Rule-based guard enforcing valid values / defaults."""
    if not spec.part_name or not spec.part_name.strip():
        raise ValueError("part_name must be a non-empty string.")
    spec.part_name = spec.part_name.strip()
    spec.material = (spec.material or "PLA").strip() or "PLA"
    spec.unit = spec.unit or CadSpec.model_fields["unit"].default
    spec.primary_workplane = (
        spec.primary_workplane or CadSpec.model_fields["primary_workplane"].default
    )
    return spec


def extract_and_plan(state: AgentState) -> AgentState:
    llm = _build_llm()
    system = SystemMessage(content=_load_prompt())
    human = HumanMessage(content=state["input_text"])

    result = llm.invoke([system, human])

    if result.get("parsing_error"):
        return {"error": f"LLM output failed to parse: {result['parsing_error']}"}

    parsed = result["parsed"]
    if parsed is None:
        return {"error": "LLM returned an empty response."}

    try:
        spec = _coerce(parsed)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}

    return {"spec": spec.model_dump(mode="json")}


def validate_and_default(state: AgentState) -> AgentState:
    try:
        spec = CadSpec.model_validate(state["spec"])
        spec = _coerce(spec)
    except Exception as exc:  # noqa: BLE001
        return {"error": str(exc)}
    return {"spec": spec.model_dump(mode="json")}


def write_json(state: AgentState) -> AgentState:
    out_path = Path(__file__).parent / "out" / "intermediate" / "spec.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(state["spec"], indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {}


def error_node(state: AgentState) -> AgentState:
    print(f"[agent error] {state.get('error', 'unknown error')}")
    return {}


def build_graph():
    builder = StateGraph(AgentState)
    builder.add_node("extract_and_plan", extract_and_plan)
    builder.add_node("validate_and_default", validate_and_default)
    builder.add_node("write_json", write_json)
    builder.add_node("error", error_node)

    builder.add_edge(START, "extract_and_plan")
    builder.add_conditional_edges(
        "extract_and_plan",
        lambda s: "error" if s.get("error") else "validate_and_default",
        {"validate_and_default": "validate_and_default", "error": "error"},
    )
    builder.add_conditional_edges(
        "validate_and_default",
        lambda s: "error" if s.get("error") else "write_json",
        {"write_json": "write_json", "error": "error"},
    )
    builder.add_edge("write_json", END)
    builder.add_edge("error", END)

    return builder.compile()


def plan(text: str) -> Dict[str, Any]:
    graph = build_graph()
    result = graph.invoke({"input_text": text})
    if not result.get("spec"):
        raise RuntimeError(result.get("error", "Agent failed to produce a spec."))
    return result["spec"]