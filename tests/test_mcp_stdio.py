"""Exercise the installed MCP entry point across a real stdio connection."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import jsonschema
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


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
    args = ["-m", "slop_guard"]
    if preset is not None:
        args.extend(["--preset", preset])
    server = StdioServerParameters(command=sys.executable, args=args, cwd=str(tmp_path))

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
