# slop-guard

[![Upstream Docs](https://img.shields.io/badge/upstream%20docs-GitHub%20Pages-0f706f?style=flat-square&logo=githubpages&logoColor=white)](https://eric-tramel.github.io/slop-guard/docs/)

A rule-based prose linter that scores text 0--100 for formulaic AI writing patterns. No LLM judge, no API calls. Purely programmatic.

The default pipeline loads 24 configurable rules backed by 200+ literal and structural heuristics. It returns a numeric score, a band label, specific violations with surrounding context, and concrete advice for each hit.

## Add to Your Agent

This is the `mlgill/slop-guard` fork of [Eric Tramel's project](https://github.com/eric-tramel/slop-guard). Its `writing_quality` and `all` presets require this fork. The unqualified PyPI package can have different features; an existing installed tool can also change what a bare `uvx slop-guard` launches.

Both clients can launch this fork with `uvx --from git+https://github.com/mlgill/slop-guard@main slop-guard`. For a persistent executable, see [Installation](#installation).
If you want a custom rule JSONL, append `-c /path/to/config.jsonl`.

### Claude Code

Add from the command line:

```bash
claude mcp add slop-guard -- uvx --from git+https://github.com/mlgill/slop-guard@main slop-guard
```

Add to your `.mcp.json`:

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

### Codex

Add from the command line:

```bash
codex mcp add slop-guard -- uvx --from git+https://github.com/mlgill/slop-guard@main slop-guard
```

Add to your `~/.codex/config.toml`:

```toml
[mcp_servers.slop-guard]
command = "uvx"
args = ["--from", "git+https://github.com/mlgill/slop-guard@main", "slop-guard"]
```

Replace `@main` with `@<full-commit-sha>` to pin a revision of this fork. Append `--preset writing_quality` or `--preset all` to the server arguments to select those rules. The default preset checks the original slop rules.

## CLI

The `sg` command lints prose from the terminal. No API keys, no network calls.

### Quick start

```bash
# Run without installing
uvx --from git+https://github.com/mlgill/slop-guard@main sg README.md

# Or install it
uv tool install --from git+https://github.com/mlgill/slop-guard@main slop-guard
sg README.md
```

### Usage

```
sg [OPTIONS] INPUT [INPUT ...]
```

`sg` requires at least one input. Each input can be a file path, `-` for stdin, or quoted inline prose text:

```bash
sg "This is some test text"
echo "Latency dropped from 180 ms to 95 ms." | sg -
```

Lint multiple files at once (shell-level glob expansion):

```bash
sg docs/*.md README.md
sg path/**/*.md
```

### Options

| Flag | Description |
|------|-------------|
| `-j`, `--json` | Output results as JSON, including `source` as the raw inline/stdin text or full file path |
| `-v`, `--verbose` | Show individual violations and advice |
| `-q`, `--quiet` | Only print sources that fail the threshold |
| `-t SCORE`, `--threshold SCORE` | Minimum passing score (0-100). Exit 1 if any input scores below this |
| `-c JSONL`, `--config JSONL` | Path to JSONL rule configuration. Defaults to packaged settings |
| `-s`, `--score-only` | Print only numeric score output |
| `--counts` | Show per-rule hit counts in the summary line |

### Examples

```bash
# One-line summary per file
sg draft.md
# => draft.md: 72/100 [light] (1843 words) *

# Score-only output
sg -s draft.md

# Use a custom rule config
sg -c /path/to/config.jsonl draft.md

# Verbose output with violations and advice
sg -v draft.md

# JSON for scripting
sg -j report.md | jq '.score'

# JSON preserves the true CLI input identity
sg -j "The migration finished in 12 seconds." | jq '.source'
# => "The migration finished in 12 seconds."

# CI gate: fail if any file scores below 60
sg -t 60 docs/*.md

# Quiet mode: only show failures
sg -q -t 60 **/*.md
```

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (all files pass threshold, or no threshold set) |
| 1 | One or more files scored below the threshold |
| 2 | Error (bad file path, read failure, etc.) |

## Fit Rule Configs (`sg-fit`)

Use `sg-fit` to fit a rule JSONL config from corpus data:

```bash
# Legacy shorthand
sg-fit TARGET_CORPUS OUTPUT

# Multi-input mode (for shell-expanded globs or many files)
sg-fit --output OUTPUT TRAIN_INPUT [TRAIN_INPUT ...]
```

Example:

```bash
sg-fit data.jsonl rules.fitted.jsonl
sg-fit --output rules.fitted.jsonl **/*.txt **/*.md
```

Optional arguments:

- `--init JSONL`: Start from a specific rule config JSONL instead of packaged defaults.
- `--negative-dataset INPUT [INPUT ...]`: Add negative dataset inputs. This flag can be repeated; all negative rows are normalized to label `0`.
- `--no-calibration`: Skip post-fit contrastive penalty calibration for faster fitting on large corpora.
- `--output JSONL`: Required when you pass more than one training input.

Target corpus rows can be either:

```json
{"text": "body of text", "label": 1}
```

or:

```json
{"text": "body of text"}
```

If `label` is omitted in the target corpus, `sg-fit` treats it as `1` (positive/target style).

`sg-fit` also accepts `.txt` and `.md` files. Each file is normalized into a single training sample.

## Installation

Requires [uv](https://docs.astral.sh/uv/).

Run once from this fork:

```bash
uvx --from git+https://github.com/mlgill/slop-guard@main slop-guard
# MCP server with custom rule config
uvx --from git+https://github.com/mlgill/slop-guard@main slop-guard -c /path/to/config.jsonl
```

Install persistently (gives you `slop-guard`, `sg`, and `sg-fit`):

```bash
uv tool install --from git+https://github.com/mlgill/slop-guard@main slop-guard
uv tool dir --bin
```

Use the absolute `slop-guard` executable path in the printed bin directory as the MCP `command`, with `args = []` for the default preset. For example, if the directory is `/Users/you/.local/bin`, use `/Users/you/.local/bin/slop-guard`. Do not put `~` in a client command that does not expand it.

This option lets a desktop client start the installed executable directly, without invoking `uvx` each time. On macOS, client startup then uses the installed executable path even when the `uv` launcher changes. Verify tool calls after installation and upgrades as described below. A working existing setup needs no reconfiguration.

Pin a revision of this fork for repeatable installation:

```bash
uv tool install --from 'git+https://github.com/mlgill/slop-guard@<full-commit-sha>' slop-guard
```

To replace an existing installation with a selected fork revision, use the same explicit source and `--force`:

```bash
uv tool install --force --from 'git+https://github.com/mlgill/slop-guard@<full-commit-sha>' slop-guard
```

### From source

From a local checkout:

```bash
uv run slop-guard               # MCP server
uv run slop-guard -c config.jsonl
uv run sg            # CLI linter
uv run sg-fit data.jsonl rules.fitted.jsonl
```

The checked-in `.mcp.json` is a development entry for this checkout. Start the client from the repository root; `uv run slop-guard` resolves that project's dependencies. It contains no developer-specific absolute path. The examples above are for configuring the fork in other projects.

### Verify the selected installation

Run the selected executable with `--help` and confirm it lists `--preset`. Then restart or reconnect the MCP client, list its tools, and call both `check_slop` and `check_slop_file` with a small prose sample. A successful process start or `--version` alone does not prove that a tool result passes MCP output validation. The test suite exercises these calls over stdio with the default, `writing_quality`, and `all` presets.

Core development workflows are also exposed through `make`:

```bash
make sync
make check
make fix
make build
make verify-wheel
```

## MCP Tools

`check_slop(text)`: Analyze a string. Returns JSON diagnostics only; it does not repeat the input text.

`check_slop_file(file_path)`: Read a file from disk and analyze it. Same output, without repeating the file path in the payload.

## What it catches

The default rules cover stock hype words and boilerplate phrases, assistant tone markers, unattributed weasel phrasing, AI self-disclosure, placeholder text, bullet/blockquote/horizontal-rule-heavy Markdown structures, arbitrary mid-sentence keyword bold, sentence and paragraph rhythm, and em dash or colon overuse.

They also flag contrast/setup-resolution tells, pithy fragments, repeated 4-8 word phrases, copula chains, extreme long sentences, aphoristic closers, and uneven paragraph cadence.

Texts under 10 words are skipped and return a clean `100`.

Otherwise scoring uses exponential decay: `score = 100 * exp(-lambda * density)`, where density is the weighted penalty sum normalized per 1000 words. Claude-specific categories (contrast pairs, setup-resolution, pithy fragments) get a concentration multiplier. Repeated use of the same tic costs more than diverse violations.

## Scoring bands

| Score | Band |
|-------|------|
| 80-100 | Clean |
| 60-79 | Light |
| 40-59 | Moderate |
| 20-39 | Heavy |
| 0-19 | Saturated |

## Output

CLI `--json` output and MCP tool responses share this structure:

```
source         CLI JSON only; raw inline/stdin text or full file path
score          0-100 integer
band           "clean" / "light" / "moderate" / "heavy" / "saturated"
word_count     integer
violations     array of {type, rule, match, context, penalty, start, end}
counts         per-category violation counts
total_penalty  sum of all penalty values
weighted_sum   after concentration multiplier
density        weighted_sum per 1000 words
advice         array of advice strings, one per distinct issue
```

MCP tool responses omit `source`, because the tool transport already carries the
input parameter.

`violations[].type` is always `"Violation"` for typed records.

## Benchmark snapshot

Example score distribution from `benchmark/us_pd_newspapers_histogram.py` on
`PleIAs/US-PD-Newspapers` (first 9,001 rows of one local shard):

![slop-guard score histogram](benchmark/output/score_histogram.white.png)

Example score-vs-length scatter plot from
`benchmark/us_pd_newspapers_scatter.py` on the same shard:

![slop-guard score vs length scatter](benchmark/output/score_vs_length_scatter.white.png)

Example per-rule compute-time curves from `benchmark/compute-time.py` +
`benchmark/chart.py` (annotated with the slowest rules at max length):

![slop-guard per-rule compute time](benchmark/output/rule_compute_time_curves.png)

## License

MIT

## Acknowledgements

- [@secemp9](https://x.com/secemp9) for his original [anti-slop rubric](https://github.com/secemp9/rubrics/blob/main/special_ones/anti_slop_rubric.xml) and inspiration.
- [@myainotez](https://x.com/myainotez) for their contributions and many helpful conversations about the project.
