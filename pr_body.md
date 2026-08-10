## Description

This PR adds a second packaged rule pipeline, `writing_quality.jsonl`, alongside the existing `default.jsonl`. The new pipeline registers fourteen opinionated writing rules from issue #9. Coverage spans qualifier words, verbose phrases, pretentious vocabulary with replacements, redundant pairs, clichés, foreign and Latin phrases, and ecstatic adjectives. The pipeline also flags throat-clearing, over-explanation, two-tier passive voice, sentences over 40 words (capped at five hits), exclamation density, emoji in prose, and narrative-poetic Markdown headings. Each rule honors the issue's per-family penalty (-1 to -4) and, where applicable, surfaces a concrete replacement in advice.

Every Rule subclass now carries a `category` class attribute (`ai_slop` or `writing_quality`). The pipeline tags each emitted violation with the producing rule's category, and the analyzer aggregates per-category counts into a new `category_counts` field. Both extras are emitted only when the active pipeline includes a non-default category, so default-only output stays byte-shape-identical to `main`.

## Why?

I was looking for a way to scrub passive voice out of long-form drafts and ran into this feature request, which already laid out a coherent rule set. Instead of writing yet another one-off linter, I implemented the issue against this codebase. The rule families overlap with my own day-to-day editing checklist (Strunk & White omit-needless-words, Orwell's plain English, Zinsser on throat-clearing), and slop-guard's existing pipeline architecture is a clean fit.

If there's interest in merging this upstream, I'm happy to iterate on it. If not, the fork at [mlgill/slop-guard](https://github.com/mlgill/slop-guard) can keep maintaining the writing-quality preset separately and stay in sync with `main` — let me know which direction you prefer.

## Usage / Demonstration

The default `ai_slop` preset is unchanged and still loads automatically:

```bash
sg draft.md
```

Opt into the writing-quality preset with the new `--preset` flag:

```bash
sg --preset writing_quality draft.md
```

Run both presets together:

```bash
sg --preset all draft.md
```

The same `--preset` flag works for the MCP server (`uvx slop-guard --preset writing_quality`).

Real example, both presets active on a 20-word sample:

```text
This crucial paradigm is groundbreaking. It is obvious that we should
utilize the methodology in order to move the needle.
```

```
sample.md: 0/100 [saturated] (20 words)
  slop_word: crucial (-2)
  slop_word: paradigm (-2)
  slop_word: groundbreaking (-2)
  pretentious_word: utilize (-2)
  pretentious_word: methodology (-2)
  verbose_phrase: in order to (-2)
  over_explanation: it is obvious that (-2)
  cliche_phrase: move the needle (-2)
  - Replace 'utilize' with 'use'.
  - Replace 'methodology' with 'method'.
  - Replace 'in order to' with 'to'.
  - Cut 'it is obvious that' — state the claim without prefacing it as obvious.
  - Cut 'move the needle' — name the concrete idea the cliché stands in for.
```

The same run via JSON includes the category aggregation:

```json
{
  "score": 0,
  "category_counts": {"ai_slop": 3, "writing_quality": 5},
  "violations": [
    {"rule": "slop_word", "category": "ai_slop", "match": "crucial", ...},
    {"rule": "pretentious_word", "category": "writing_quality", "match": "utilize", ...}
  ]
}
```

When only the default `ai_slop` preset runs, neither `category` nor `category_counts` appears — the JSON shape matches the pre-PR release exactly.

## Verification

- `make check` passes: 226 tests, ruff format and lint clean, ty type-check clean, 83.18% coverage (above the 80% gate).
- 32 new targeted tests in `tests/test_opinionated_rules.py` covering replacement-aware advice, the long-sentence cap, the passive-voice tier-two density gate, exclamation-density threshold, per-emoji emission, hyphenated and multi-word matching, and fit paths for every new rule.
- 12 category tests in `tests/test_categories.py` covering both directions of tagging, mixed pipelines, conditional `category_counts` emission, and disjoint catalog partitioning.
- Smoke-tested both presets via `sg -j` and `sg -v` on the same input. Default JSON output verified to match `main` byte-for-byte (no `category` keys, no `category_counts`).
- Generated `docs/rules/*.md` pages for the fourteen new rules via `make docs-rules`. The 24 existing rule pages are untouched.
- Self-linted `README.md`, `docs/get-started.md`, and `docs/agents.md` against both presets; all score in the clean band except a few honest hits where the prose literally cites the phrases its own rules flag.

## Issues

- Closes #9.
