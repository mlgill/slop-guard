"""Helpers for resolving packaged rule presets by short name.

The CLI and MCP entry points expose ``--preset NAME`` as an ergonomic
alternative to ``--config /path/to/file.jsonl``. Names map to packaged
JSONL assets shipped inside the ``slop_guard.rules`` package, so users
do not need to resolve absolute paths themselves.
"""

from importlib.resources import files
from pathlib import Path

from .pipeline import Pipeline

SINGLE_PRESET_NAMES: tuple[str, ...] = ("default", "writing_quality")
PRESET_CHOICES: tuple[str, ...] = ("default", "writing_quality", "all")


def preset_jsonl_path(name: str) -> Path:
    """Return the absolute path of a single packaged preset JSONL.

    Args:
        name: One of ``"default"`` or ``"writing_quality"``.

    Returns:
        Filesystem path to the bundled JSONL.

    Raises:
        ValueError: ``name`` is not a known single-preset name.
    """
    if name not in SINGLE_PRESET_NAMES:
        raise ValueError(
            f"Unknown preset {name!r}. Known presets: {', '.join(SINGLE_PRESET_NAMES)}."
        )
    return Path(str(files("slop_guard.rules").joinpath(f"assets/{name}.jsonl")))


def load_preset(name: str) -> Pipeline:
    """Build a Pipeline for a packaged preset name.

    The ``"all"`` preset concatenates rules from the ``default`` and
    ``writing_quality`` JSONLs in order, so the default ai_slop rules run
    first followed by the writing-quality rules.

    Args:
        name: One of ``"default"``, ``"writing_quality"``, or ``"all"``.

    Returns:
        Loaded rule pipeline.

    Raises:
        ValueError: ``name`` is not a known preset.
    """
    if name == "all":
        rules: list = []
        for single in SINGLE_PRESET_NAMES:
            rules.extend(Pipeline.from_jsonl(preset_jsonl_path(single)).rules)
        return Pipeline(rules)
    if name in SINGLE_PRESET_NAMES:
        return Pipeline.from_jsonl(preset_jsonl_path(name))
    raise ValueError(
        f"Unknown preset {name!r}. Known presets: {', '.join(PRESET_CHOICES)}."
    )
