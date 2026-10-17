---
icon: lucide/bot
---

# Agents

Both supported clients can select the `mlgill/slop-guard` fork explicitly:

```bash
uvx --from git+https://github.com/mlgill/slop-guard@main slop-guard
```

That starts the local MCP server without any API calls or model-side judging. The tools return structured diagnostics that agents can use while they draft docs, release notes, or status updates.

The MCP surface is small on purpose. Agents can call `check_slop` when they already have text in memory, or `check_slop_file` when they need to inspect a file on disk. Both tools return structured JSON, so the client can point at exact spans and feed the advice back into the rewrite loop.

## Codex

Add this source-qualified command to `~/.codex/config.toml`:

```toml
[mcp_servers.slop-guard]
command = "uvx"
args = ["--from", "git+https://github.com/mlgill/slop-guard@main", "slop-guard"]
```

## Claude Code

Add this source-qualified command to `.mcp.json`:

```json
{
  "mcpServers": {
    "slop-guard": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mlgill/slop-guard@main", "slop-guard"]
    }
  }
}
```

## Choose a rule preset

The MCP server reads the same `--preset` flag as the CLI. The default preset checks the original rules; `--preset writing_quality` selects the opinionated style checks, and `--preset all` runs both. Both tools also accept a per-call `profile` selector, so one server can expose all presets. Existing separate entries remain supported.

The [writing profiles](writing-profiles.md) add `casual`, `professional-email`, and `leadership-update`. Use `slop-guard --preset casual --require-absolute-paths` for a plugin whose server working directory may differ from the caller's workspace. Always send absolute paths to that server. Assess any returned `review_requirements` before claiming the draft meets the chosen profile; deterministic scoring does not perform that review.

Codex `~/.codex/config.toml`:

```toml
[mcp_servers.slop-guard]
command = "uvx"
args = ["--from", "git+https://github.com/mlgill/slop-guard@main", "slop-guard"]

[mcp_servers.slop-guard-writing-quality]
command = "uvx"
args = ["--from", "git+https://github.com/mlgill/slop-guard@main", "slop-guard", "--preset", "writing_quality"]
```

Claude Code `.mcp.json`:

```json
{
  "mcpServers": {
    "slop-guard": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mlgill/slop-guard@main", "slop-guard"]
    },
    "slop-guard-writing-quality": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/mlgill/slop-guard@main", "slop-guard", "--preset", "writing_quality"]
    }
  }
}
```

When the active pipeline includes any non-default preset, each violation the MCP tool returns carries a `category` field (`"ai_slop"` or `"writing_quality"`) and `category_counts` aggregates violations per category. For the default preset, MCP serialization can supply `null` for these optional fields; CLI output omits them.

## Pin a fork revision

If an automation or team workflow needs a fixed revision, replace `@main` with a full commit SHA from this fork:

```bash
uvx --from 'git+https://github.com/mlgill/slop-guard@<full-commit-sha>' slop-guard
```

An upstream PyPI release does not select this fork. A bare `uvx slop-guard` may reuse a previously installed tool, so checking it on one machine does not establish what a fresh setup will run.

Every published docs page also exposes a raw Markdown sibling at the same slug. For example, the rendered `get-started` page lives alongside `/docs/get-started.md`, which makes scripted crawling easier for agents and automation.

## Use an installed executable

Install the fork with the command in [Get started](get-started.md#install-the-cli), then run `uv tool dir --bin`. Set the MCP command to the absolute `slop-guard` path in that directory; use no arguments for the default preset, or `["--preset", "writing_quality"]` for that preset. This starts the executable directly, so a desktop client does not invoke `uvx` on every connection. Keep a working existing configuration unless you intend to change it.

After installation or an upgrade, confirm `--help` lists `--preset`, reconnect the client, list its tools, and call `check_slop` and `check_slop_file` with a prose sample. Verify successful structured results; server startup alone does not test the output schema.

The repository's tracked `.mcp.json` is a separate development entry. Start the client from the repository root to run `uv run slop-guard` against the checkout. The file contains no machine-specific absolute path.
