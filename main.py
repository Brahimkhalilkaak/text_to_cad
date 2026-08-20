"""CLI entry point for the text-to-CAD pipeline.

Runs the whole chain: text -> spec.json -> build123d code -> STL.

Usage:
    python main.py "i want a box with 10mm*10mm*10mm with a hole"
"""

import json
import sys
from pathlib import Path

from cad_planner import plan
from cad_coder import OUT_DIR, generate

OUT_PATH = Path(__file__).parent / "out" / "intermediate" / "spec.json"


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print('usage: python main.py "<part description>"', file=sys.stderr)
        return 1
    text = " ".join(args)

    try:
        spec = plan(text)
    except Exception as exc:  # noqa: BLE001
        print(f"[error] {exc}", file=sys.stderr)
        return 1

    OUT_PATH.write_text(
        json.dumps(spec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(spec, indent=2, ensure_ascii=False))
    print(f"\n[written] {OUT_PATH}")

    try:
        code_path = generate(spec)
    except Exception as exc:  # noqa: BLE001
        print(f"[cad_coder error] {exc}", file=sys.stderr)
        return 1
    print(f"[written] {code_path}")
    stl_path = OUT_DIR / "generated_part.stl"
    print(f"[written] {stl_path}" if stl_path.exists() else "[missing] STL not produced")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())