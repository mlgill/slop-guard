"""Exercise the installed MCP entry point across a real stdio connection."""

from __future__ import annotations

import asyncio
import json
import os
import sys
import sysconfig
from pathlib import Path

import jsonschema
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from slop_guard.rules.presets import PRESET_CHOICES


@pytest.mark.parametrize("preset", [None, "writing_quality", "all"])
def test_installed_server_returns_valid_results_over_stdio(
    tmp_path: Path, preset: str | None
) -> None:
    """Check both tools and preset selection outside the repository directory.

    Args:
        tmp_path: Temporary working directory and prose fixture location.
        preset: Explicit fork preset, or None for the default launch.
    """
    text = "This comprehensive solution leverages best practices. It is very important."
    target = tmp_path / "sample prose.md"
    target.write_text(text, encoding="utf-8")
    executable = Path(sysconfig.get_path("scripts")) / (
        "slop-guard.exe" if os.name == "nt" else "slop-guard"
    )
    assert executable.is_file()
    args: list[str] = []
    if preset is not None:
        args.extend(["--preset", preset])
    server = StdioServerParameters(
        command=str(executable), args=args, cwd=str(tmp_path)
    )

    async def exercise() -> None:
        """Initialize, discover tools, and validate their wire-format results."""
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                assert {tool.name for tool in tools} == {
                    "check_slop",
                    "check_slop_file",
                }
                schemas = {tool.name: tool.outputSchema for tool in tools}
                for name, arguments in [
                    ("check_slop", {"text": text}),
                    ("check_slop_file", {"file_path": str(target)}),
                ]:
                    result = await session.call_tool(name, arguments)
                    assert not result.isError, result.content
                    payload = result.structuredContent
                    assert payload is not None
                    assert schemas[name] is not None
                    jsonschema.validate(payload, schemas[name])
                    assert 0 <= payload["score"] <= 100
                    assert payload["word_count"] > 0
                    assert payload["violations"]
                    if preset is not None:
                        assert isinstance(payload["category_counts"], dict)
                        assert any(
                            row["category"] == "writing_quality"
                            for row in payload["violations"]
                        )
                invalid = await session.call_tool(
                    "check_slop_file", {"file_path": str(tmp_path / "missing.txt")}
                )
                assert invalid.isError

    asyncio.run(exercise())


def test_profile_selection_and_absolute_file_contract_over_stdio(
    tmp_path: Path,
) -> None:
    """Validate every profile, pending guidance, and errors through installed MCP."""
    executable = Path(sysconfig.get_path("scripts")) / (
        "slop-guard.exe" if os.name == "nt" else "slop-guard"
    )
    text = (
        "Bottom line: we should utilize the report in order to finish the review. "
        "The operator compared each record against the original table and found "
        "a missing value near the end. She saved the corrected total, sent the "
        "report for review, and asked the team to check the remaining entries "
        "before making a decision about the next batch."
    )
    target = tmp_path / "sample.md"
    target.write_text(text, encoding="utf-8")
    server = StdioServerParameters(
        command=str(executable),
        args=["--preset", "casual", "--require-absolute-paths"],
        cwd=str(tmp_path),
    )

    async def exercise_profiles() -> None:
        """Exercise per-call selection without mutating startup configuration."""
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                schemas = {
                    tool.name: tool.outputSchema
                    for tool in (await session.list_tools()).tools
                }
                for profile in PRESET_CHOICES:
                    for tool, arguments in (
                        ("check_slop", {"text": text}),
                        ("check_slop_file", {"file_path": str(target)}),
                    ):
                        result = await session.call_tool(
                            tool, arguments | {"profile": profile}
                        )
                        assert not result.isError, result.content
                        payload = result.structuredContent
                        assert payload is not None
                        jsonschema.validate(payload, schemas[tool])
                        assert payload["profile"] == profile
                        if profile in {
                            "casual",
                            "professional-email",
                            "leadership-update",
                        }:
                            assert payload["review_requirements"]
                            assert any(
                                row["category"] == "writing_quality"
                                for row in payload["violations"]
                            )
                        else:
                            assert payload["review_requirements"] == []
                    bad = await session.call_tool(
                        "check_slop", {"text": text, "profile": "typo"}
                    )
                    assert bad.isError
                for tool, arguments in (
                    ("check_slop", {"text": "Hello world"}),
                    ("check_slop_file", {"file_path": str(target)}),
                ):
                    result = await session.call_tool(tool, arguments)
                    assert not result.isError
                    assert result.structuredContent is not None
                    assert result.structuredContent["profile"] == "casual"
                    jsonschema.validate(result.structuredContent, schemas[tool])
                relative = await session.call_tool(
                    "check_slop_file", {"file_path": "sample.md"}
                )
                assert relative.isError

    asyncio.run(exercise_profiles())


def test_development_config_launches_from_checkout() -> None:
    """Launch the tracked developer entry with the current test environment."""
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"][
        "slop-guard-dev"
    ]
    server = StdioServerParameters(
        command=config["command"],
        args=config["args"],
        cwd=str(root),
        # Tests already have the project's dependencies. Reuse that environment
        # without syncing, installing, or changing a caller's local .venv.
        env={"UV_PROJECT_ENVIRONMENT": sys.prefix, "UV_NO_SYNC": "1"},
    )

    async def exercise() -> None:
        """Check the configured command reaches the public tool boundary."""
        async with stdio_client(server) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = (await session.list_tools()).tools
                result = await session.call_tool("check_slop", {"text": "Hello world"})
                assert not result.isError, result.content
                schema = next(
                    tool.outputSchema for tool in tools if tool.name == "check_slop"
                )
                assert result.structuredContent is not None
                assert schema is not None
                jsonschema.validate(result.structuredContent, schema)

    asyncio.run(exercise())
