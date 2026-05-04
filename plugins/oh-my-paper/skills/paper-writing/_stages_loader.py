"""
Dynamic Stage Loader — scans the stages/ directory structure and loads
stage metadata + writing prompts for each sub-folder.
Mirrors the ArXiv paper reader's skills/loader.py pattern.
"""

from pathlib import Path
from typing import Any

METADATA_FILE = "_metadata.md"
WRITING_PROMPT_FILE = "writing_prompt.md"

# ── Path resolution ─────────────────────────────────────────────


def _get_stages_dir() -> Path:
    """Return the stages/ directory relative to this file."""
    return Path(__file__).parent / "stages"


def _read_md(path: Path) -> str:
    """Read a markdown file, return empty string if missing."""
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


# ── Core API ───────────────────────────────────────────────────


def load_all_stages() -> dict[str, dict[str, Any]]:
    """
    Load every writing stage from the stages/ directory.

    Returns:
        {
            "01-background": {
                "name": "01-background",
                "metadata": "<content of _metadata.md>",
                "writing_prompt": "<content of writing_prompt.md>",
                "order": 1,
            },
            ...
        }
    """
    stages_dir = _get_stages_dir()
    stages: dict[str, dict[str, Any]] = {}

    if not stages_dir.exists():
        return stages

    for child in sorted(stages_dir.iterdir()):
        if child.is_dir() and not child.name.startswith("_"):
            metadata = _read_md(child / METADATA_FILE)
            writing_prompt = _read_md(child / WRITING_PROMPT_FILE)

            if not metadata:
                continue

            # Extract order from folder name (e.g., "01-background" -> 1)
            order = 99
            parts = child.name.split("-")
            if parts and parts[0].isdigit():
                order = int(parts[0])

            stages[child.name] = {
                "name": child.name,
                "metadata": metadata,
                "writing_prompt": writing_prompt,
                "order": order,
            }

    return stages


def get_stage_writing_prompt(stage_name: str) -> str:
    """
    Get the writing prompt for a specific stage.

    Args:
        stage_name: Folder name like "01-background", "06-practice"

    Returns:
        The content of writing_prompt.md, or empty string if not found.
    """
    stages = load_all_stages()
    return stages.get(stage_name, {}).get("writing_prompt", "")


def get_stage_metadata(stage_name: str) -> str:
    """
    Get the metadata description for a specific stage.

    Args:
        stage_name: Folder name like "01-background"

    Returns:
        The content of _metadata.md, or empty string if not found.
    """
    stages = load_all_stages()
    return stages.get(stage_name, {}).get("metadata", "")


def get_all_stages_ordered() -> list[dict[str, Any]]:
    """
    Return all stages sorted by their order number.

    Returns:
        List of stage dicts, sorted by "order" ascending.
    """
    stages = load_all_stages()
    return sorted(stages.values(), key=lambda x: x["order"])


def get_stages_description() -> str:
    """
    Build a textual description of all stages (used by stage classifier / overview).
    """
    lines: list[str] = []
    for info in get_all_stages_ordered():
        lines.append(f"### {info['name']}\n{info['metadata']}\n")
    return "\n".join(lines)
