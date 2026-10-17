"""Behavioral calibration fixtures for explicit audience writing profiles.

These synthetic examples protect stated preferences; they are not user-authored
samples or evidence of a completed semantic review.
"""

import io
import json
import os
import subprocess
import sysconfig
from dataclasses import replace
from pathlib import Path

import pytest

from slop_guard.apps import cli, hook
from slop_guard.document import AnalysisDocument
from slop_guard.engine import analyze_text
from slop_guard.rules.passage.substantial_prose_style import SubstantialProseStyleRule
from slop_guard.rules.pipeline import Pipeline
from slop_guard.rules.presets import PROFILE_NAMES, load_preset
from slop_guard.rules.prose import ProsePipeline

GOOD = (
    "The model was trained on 2,000 sequences. The report that contains the revised "
    "total is attached. Today we measured 18 ms; tomorrow we will repeat the experiment. "
    "Preliminary results suggest a smaller memory requirement. I checked the artifact "
    "provenance and linked the [source](https://example.com). We still need measurements "
    "from the larger sample before drawing a conclusion."
)
BAD = (
    "Bottom line: this is a game-changing solution. Here's the thing: we will think "
    "outside the box in order to move the needle. This isn't about tooling. It's about "
    "excellence. The simplest mental model is a team working through a long list of "
    "requests while the operator writes a report for the reviewer at the end of the week."
)


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_profiles_preserve_natural_technical_prose(profile: str) -> None:
    """Grammar, uncertainty, references, and technical terms remain unpenalized."""
    result = analyze_text(GOOD, pipeline=load_preset(profile))
    assert result["violations"] == []
    assert result["score"] == 100
    requirement = result["review_requirements"][0]
    assert "Pending" in requirement["reason"]
    assert {item["key"] for item in requirement["criteria"]} == {
        "plain_language",
        "direct_and_connected",
        "facts_and_uncertainty",
        "natural_structure",
        "revision",
        "audience",
    }


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_profiles_find_stock_prose_with_exact_source_spans(profile: str) -> None:
    """Bad prose triggers distinct rules and keeps semantic review after tagging."""
    result = analyze_text(BAD, pipeline=load_preset(profile))
    assert result["score"] < 100
    assert result["category_counts"]
    assert result["review_requirements"]
    assert {row["rule"] for row in result["violations"]} >= {
        "substantial_prose_style",
        "cliche_phrase",
        "setup_resolution",
        "verbose_phrase",
    }
    for row in result["violations"]:
        assert BAD[row["start"] : row["end"]].casefold() == row["match"].casefold()
    substantial = [
        row["match"].lower()
        for row in result["violations"]
        if row["rule"] == "substantial_prose_style"
    ]
    assert "move the needle" not in substantial


def test_profile_intensity_and_audience_are_explicit_and_distinct() -> None:
    """Casual checks are lighter; leadership catches repeated report phrasing."""
    pipelines = {name: load_preset(name) for name in PROFILE_NAMES}
    results = {
        name: analyze_text(BAD, pipeline=value) for name, value in pipelines.items()
    }
    assert (
        results["casual"]["total_penalty"]
        > results["professional-email"]["total_penalty"]
    )
    audience = {
        name: result["review_requirements"][0]["criteria"][-1]["instruction"]
        for name, result in results.items()
    }
    assert len(set(audience.values())) == 3
    repeated = "The sample contains several missing measurements. The sample contains several missing measurements."
    assert (
        analyze_text(repeated, pipeline=pipelines["casual"])["counts"]["phrase_reuse"]
        == 0
    )
    assert (
        analyze_text(repeated, pipeline=pipelines["leadership-update"])["counts"][
            "phrase_reuse"
        ]
        > 0
    )


def test_threshold_masks_code_and_records_no_false_review_completion() -> None:
    """Only prose words count and the threshold is inclusive at fifty."""
    rule = load_preset("casual").rules[-1]
    text = " ".join(f"word{index}" for index in range(49))
    assert not rule.forward(AnalysisDocument.from_text(text)).review_requirements
    coded = (
        text
        + " `Bottom line: game-changing`\n```text\n"
        + GOOD
        + "\n```\n<code>"
        + GOOD
        + "</code>"
    )
    assert not rule.forward(AnalysisDocument.from_text(coded)).review_requirements
    result = rule.forward(AnalysisDocument.from_text(text + " fiftieth"))
    assert result.review_requirements
    assert result.violations == []


def test_configured_phrase_cap_and_boundaries() -> None:
    """Caps limit records, not counts; substring matches do not flag larger words."""
    original = load_preset("casual").rules[-1]
    assert isinstance(original, SubstantialProseStyleRule)
    rule = SubstantialProseStyleRule(
        replace(original.config, record_cap=1, min_words=10)
    )
    text = "Bottom line: bottom line: this game-changingly word is not a match in this passage."
    result = analyze_text(text, pipeline=Pipeline([rule]))
    assert len(result["violations"]) == 1
    assert result["counts"]["substantial_prose_style"] == 2


@pytest.mark.parametrize(
    "changes",
    [
        {"min_words": 0},
        {"penalty": 1},
        {"phrases": []},
        {"semantic_criteria": []},
        {"semantic_criteria": [{"key": "x"}]},
    ],
)
def test_invalid_configuration_fails_loudly(changes: dict[str, object]) -> None:
    """User profiles require complete, valid configuration without fallbacks."""
    rule = load_preset("casual").rules[-1]
    config = rule.to_dict() | changes
    with pytest.raises(ValueError):
        SubstantialProseStyleRule.from_dict(config)


def test_cli_profile_json_and_verbose_keep_pending_review(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Both JSON and human output disclose semantic work despite a clean score."""
    assert cli.cli_main(["--preset", "professional-email", "--json", GOOD]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["profile"] == "professional-email"
    assert result["review_requirements"]
    assert cli.cli_main(["--preset", "casual", "--verbose", GOOD]) == 0
    assert "Pending semantic review:" in capsys.readouterr().out


def test_casual_short_reply_and_useful_structure_are_preserved() -> None:
    """Friendly replies, real headings, and lists should survive all profiles."""
    for profile in PROFILE_NAMES:
        for text in (
            "Thanks! I’ll check it tomorrow.",
            "## What changed?\n\n" + GOOD,
            "1. **Runtime**\n   - We measured 18 ms.\n2. **Memory**\n   - Usage fell to 4 GB.\n"
            + GOOD,
        ):
            assert not analyze_text(text, pipeline=load_preset(profile))["violations"]


def test_hook_selects_profile_without_repeating_or_blocking(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Report hooks use explicit selection and emit only a safe summary."""
    payload = json.dumps(
        {
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": BAD,
        }
    )
    monkeypatch.setattr(hook.sys, "stdin", io.StringIO(payload))
    assert hook.hook_main(["--preset", "casual"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert set(result) == {"systemMessage"}
    assert "substantial_prose_style" in result["systemMessage"]
    assert BAD not in result["systemMessage"]
    assert hook.hook_main([]) == 1


@pytest.mark.parametrize("profile", PROFILE_NAMES)
def test_code_examples_neither_trigger_nor_dilute_profile_checks(profile: str) -> None:
    """All reused rules ignore code; HTML code cannot inflate score density."""
    pipeline = load_preset(profile)
    baseline = analyze_text(GOOD, pipeline=pipeline)
    for code in (f"```text\n{BAD}\n```\n", f"<pre>{BAD}</pre>\n", f"`{BAD}`\n"):
        result = analyze_text(code + GOOD, pipeline=pipeline)
        assert result["violations"] == []
        assert result["word_count"] == baseline["word_count"]
    flagged = analyze_text(BAD, pipeline=pipeline)
    with_code = analyze_text(f"<code>{GOOD * 5}</code>\n" + BAD, pipeline=pipeline)
    assert with_code["score"] == flagged["score"]
    assert with_code["word_count"] == flagged["word_count"]
    assert (
        analyze_text(f"<pre>{BAD * 5}</pre> Thanks!", pipeline=pipeline)["word_count"]
        == 1
    )


def test_code_duplicate_cannot_capture_prose_finding_location() -> None:
    """Legacy implicit locations resolve against prose before source restoration."""
    prefix = "```text\nin order to move the needle\n```\n"
    text = prefix + BAD
    result = analyze_text(text, pipeline=load_preset("casual"))
    for row in result["violations"]:
        assert row["start"] >= len(prefix)
        assert text[row["start"] : row["end"]].casefold() == row["match"].casefold()


def test_fit_roundtrip_preserves_zero_penalties_and_code_masking(
    tmp_path: Path,
) -> None:
    """An ordinary fitted export reloads zero penalties and the prose projection."""
    pipeline = load_preset("casual")
    pipeline.fit([BAD, GOOD], [1, 0])
    assert pipeline.rules[-1].to_dict()["penalty"] == 0
    target = tmp_path / "fitted.jsonl"
    pipeline.to_jsonl(target)
    restored = Pipeline.from_jsonl(target)
    assert isinstance(restored, ProsePipeline)
    assert restored.rules[-1].to_dict()["penalty"] == 0
    text = f"<pre>{BAD}</pre>\n" + GOOD
    assert analyze_text(text, pipeline=restored) == analyze_text(
        text, pipeline=pipeline
    )


def test_profile_fit_uses_same_code_projection() -> None:
    """Code examples cannot alter learned settings or contrastive calibration."""
    ordinary = load_preset("casual").fit([GOOD, BAD], [1, 0])
    coded = load_preset("casual").fit([f"<code>{BAD}</code>\n" + GOOD, BAD], [1, 0])
    assert [rule.to_dict() for rule in coded.rules] == [
        rule.to_dict() for rule in ordinary.rules
    ]


def test_prose_header_accepts_json_whitespace_and_rejects_bad_values(
    tmp_path: Path,
) -> None:
    """Portable JSONL exports parse metadata structurally, without silent fallback."""
    target = tmp_path / "profile.jsonl"
    load_preset("casual").to_jsonl(target)
    rules = "\n".join(target.read_text().splitlines()[1:])
    target.write_text('\n  { "prose_only" : true }\n' + rules)
    assert isinstance(Pipeline.from_jsonl(target), ProsePipeline)
    for value in ("false", "1", '"true"'):
        target.write_text('{"prose_only":' + value + "}\n" + rules)
        with pytest.raises(ValueError, match="prose_only"):
            Pipeline.from_jsonl(target)


def test_installed_hook_entrypoint_is_report_only(tmp_path: Path) -> None:
    """Exercise the wheel's hook executable outside the checkout directory."""
    executable = Path(sysconfig.get_path("scripts")) / (
        "sg-hook.exe" if os.name == "nt" else "sg-hook"
    )
    payload = json.dumps(
        {
            "hook_event_name": "Stop",
            "stop_hook_active": False,
            "last_assistant_message": BAD,
        }
    )
    result = subprocess.run(
        [str(executable), "--preset", "casual"],
        input=payload,
        text=True,
        capture_output=True,
        cwd=tmp_path,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert set(json.loads(result.stdout)) == {"systemMessage"}
    assert BAD not in result.stdout
