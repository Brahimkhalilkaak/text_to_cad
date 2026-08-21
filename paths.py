"""Centralized filesystem layout shared by all agents.

Change the output/prompt locations here, not across individual modules.
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

PROMPTS_DIR = PROJECT_ROOT / "prompts"
PLANNER_PROMPT_FILE = PROMPTS_DIR / "cad_spec_planner.md"
CODER_PROMPT_FILE = PROMPTS_DIR / "cad_coder.md"

OUT_DIR = PROJECT_ROOT / "out"
INTERMEDIATE_DIR = OUT_DIR / "intermediate"
SPEC_FILE = INTERMEDIATE_DIR / "spec.json"
CODE_FILE = INTERMEDIATE_DIR / "generated_part.py"
STL_FILE = OUT_DIR / "generated_part.stl"
GRAPH_PNG = INTERMEDIATE_DIR / "graph_architecture.png"