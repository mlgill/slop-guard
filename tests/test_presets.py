"""Tests for the packaged preset loader and CLI/MCP --preset flags."""

import io
import json
from pathlib import Path
from typing import Any

import pytest

from slop_guard.apps import cli as cli_app
from slop_guard.rules.base import Rule
from slop_guard.rules.catalog import (
    DEFAULT_RULE_PATHS,
    WRITING_QUALITY_RULE_PATHS,
)
from slop_guard.rules.presets import (
    PRESET_CHOICES,
    load_preset,
    preset_jsonl_path,
)


def _qualified_rule_names(rules: list[Rule[Any]]) -> list[str]:
    """Return fully-qualified class paths for a pipeline's rules."""
    return [f"{type(r).__module__}.{type(r).__name__}" for r in rules]


def test_preset_choices_match_documented_set() -> None:
    """The CLI choices and the documented preset names should match."""
    assert set(PRESET_CHOICES) == {"default", "writing_quality", "all"}


def test_preset_jsonl_path_returns_existing_files() -> None:
    """Both single presets should resolve to readable JSONL files."""
    for name in ("default", "writing_quality"):
        path = preset_jsonl_path(name)
        assert path.exists()
        assert path.read_text(encoding="utf-8").strip()


def test_load_preset_default_matches_default_catalog() -> None:
    """The 'default' preset should load exactly the default rule paths."""
    pipeline = load_preset("default")
    assert _qualified_rule_names(pipeline.rules) == list(DEFAULT_RULE_PATHS)


def test_load_preset_writing_quality_matches_catalog() -> None:
    """The 'writing_quality' preset should load exactly the writing-quality paths."""
    pipeline = load_preset("writing_quality")
    assert _qualified_rule_names(pipeline.rules) == list(WRITING_QUALITY_RULE_PATHS)


def test_load_preset_all_concatenates_default_and_writing_quality() -> None:
    """The 'all' preset should concatenate default rules then writing-quality rules."""
    pipeline = load_preset("all")
    expected = list(DEFAULT_RULE_PATHS) + list(WRITING_QUALITY_RULE_PATHS)
    assert _qualified_rule_names(pipeline.rules) == expected


def test_load_preset_rejects_unknown_name() -> None:
    """An unknown preset name should raise ValueError with a helpful message."""
    with pytest.raises(ValueError, match="Unknown preset"):
        load_preset("nope")


def test_cli_preset_writing_quality_emits_category_field(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`sg --preset writing_quality -j` should tag every violation with the category."""
    monkeypatch.setattr(
        cli_app.sys,
        "stdin",
        io.StringIO(
            "It is obvious that we should utilize the methodology in order to "
            "move the needle on the end result."
        ),
    )
    exit_code = cli_app.cli_main(["--preset", "writing_quality", "-j", "-"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["violations"], "expected at least one violation"
    assert all(
        violation["category"] == "writing_quality"
        for violation in payload["violations"]
    )
    assert payload["category_counts"]["writing_quality"] >= 1


def test_cli_preset_all_emits_both_categories(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`sg --preset all` should emit both ai_slop and writing_quality categories."""
    monkeypatch.setattr(
        cli_app.sys,
        "stdin",
        io.StringIO(
            "This crucial paradigm is groundbreaking. "
            "It is obvious that we should utilize the methodology."
        ),
    )
    exit_code = cli_app.cli_main(["--preset", "all", "-j", "-"])
    assert exit_code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "ai_slop" in payload["category_counts"]
    assert "writing_quality" in payload["category_counts"]


def test_cli_preset_and_config_are_mutually_exclusive(tmp_path: Path) -> None:
    """Passing both -c and --preset should fail with a clear error."""
    config = tmp_path / "fake.jsonl"
    config.write_text("", encoding="utf-8")
    exit_code = cli_app.cli_main(
        ["-c", str(config), "--preset", "writing_quality", "draft text"]
    )
    assert exit_code != 0
