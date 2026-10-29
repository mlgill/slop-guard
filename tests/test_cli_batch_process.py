"""Exercise mixed file batches through the installed console entrypoint."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize("unreadable", ["missing", "invalid_utf8", "none"])
@pytest.mark.parametrize("threshold", [0, 100])
def test_cli_batch_retains_results_and_prioritizes_read_errors(
    tmp_path: Path, unreadable: str, threshold: int
) -> None:
    """Requested file failures outrank thresholds while valid results survive."""
    good = tmp_path / "good.txt"
    good.write_text(
        "Delve into this rich tapestry of transformative synergy that ultimately unlocks unprecedented potential for everyone involved in the journey.",
        encoding="utf-8",
    )
    arguments = [str(good)]
    if unreadable != "none":
        bad = tmp_path / "unreadable.txt"
        if unreadable == "invalid_utf8":
            bad.write_bytes(b"\xff\xfe\xff")
        arguments.insert(0, str(bad))
    result = subprocess.run(
        [
            str(Path(sys.executable).parent / "sg"),
            "--json",
            "-t",
            str(threshold),
            *arguments,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    assert payload["source"] == str(good)
    assert payload["score"] < 100
    expected = 2 if unreadable != "none" else (1 if threshold else 0)
    assert result.returncode == expected
    if unreadable == "missing":
        assert "No such file" in result.stderr
    elif unreadable == "invalid_utf8":
        assert "decode" in result.stderr
    else:
        assert result.stderr == ""
