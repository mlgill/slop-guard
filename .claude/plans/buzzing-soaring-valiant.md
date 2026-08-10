# Plan: Address slop-guard issue #9 with minimum-change additions

## Context

[Issue #9](https://github.com/eric-tramel/slop-guard/issues/9) proposes 13 opinionated writing-quality rule families (qualifier words, verbose phrases, passive voice, pretentious words, throat-clearing, redundant pairs, clichés, etc.). The maintainer's comment on the issue says they modularized the rule system specifically so contributors can add these.

Goal: cover as many of the issue's examples as possible **without** duplicating existing rules **and** with the smallest possible diff.

Approach: add new word/phrase strings to the existing data tuples in `slop_word.py` and `slop_phrase.py`. Skip rule families that would require a new Rule class (passive voice, exclamation density, emoji, narrative-poetic headings, 40-word sentences) — those are larger architectural additions that don't fit the "minimum change" constraint and can be follow-up PRs.

## What gets added where

### `src/slop_guard/rules/sentence/slop_phrase.py`

Append literals to `_SLOP_PHRASES_LITERAL` (the rule already iterates this tuple; no logic change needed). Each new phrase inherits the existing `-3` penalty from `default.jsonl` and the generic advice "Cut '{phrase}' — replace the setup with the actual point."

**Verbose phrases** (issue rule 2):
- `in order to`, `due to the fact that`, `at the present time`, `has the ability to`, `the vast majority of`, `whether or not`

**Throat-clearing** (issue rule 7) — only the 3 not already covered by `it's worth noting` / `it's important to note`:
- `it should be pointed out that`, `the fact of the matter is`, `truth be told`
- (`it is interesting to note that` and `one might argue that` close enough to existing entries — skip to avoid near-duplicate matches.)

**Over-explanation phrases** (issue rule 8):
- `needless to say`, `as everyone knows`, `it is obvious that`

**Redundant pairs** (issue rule 9):
- `completely destroyed`, `totally unique`, `end result`, `past history`, `close proximity`, `free gift`, `advance warning`, `true fact`, `general consensus`, `revert back`, `repeat again`

**Cliché phrases** (issue rule 10):
- `think outside the box`, `low-hanging fruit`, `move the needle`, `tip of the iceberg`, `elephant in the room`, `perfect storm`, `silver bullet`, `double-edged sword`, `hit the ground running`, `reinvent the wheel`

**Foreign/Latin phrases** (issue rule 11):
- `per se`, `vis-a-vis`, `ad hoc`, `de facto`, `status quo`

The pre-computed tuples beside `_SLOP_PHRASES_LITERAL` (`_SLOP_PHRASE_REQUIRED_PUNCT`, `_SLOP_PHRASE_LENGTHS`, `_SLOP_PHRASES_RE_LIST`) are derived via tuple comprehensions over `_SLOP_PHRASES_LITERAL`, so they update automatically.

### `src/slop_guard/rules/word/slop_word.py`

Append words to existing tuples. The rule rebuilds `_ALL_SLOP_WORDS`, `_SLOP_WORD_RE`, etc. from these tuples, so the only edit is the data lists.

**Ecstatic adjectives** (issue rule 12) — add to `_SLOP_ADJECTIVES`, skipping the three already present (`stunning`, `breathtaking`, `captivating`):
- `wonderful`, `amazing`, `incredible`, `fantastic`, `phenomenal`, `magnificent`, `mind-blowing`, `awe-inspiring`

**Pretentious verbs** (issue rule 4, verb subset) — add to `_SLOP_VERBS`:
- `utilize`, `facilitate`, `commence`, `ameliorate`

**Pretentious nouns/modifiers** (issue rule 4, noun/adj subset) — add to `_SLOP_NOUNS` / `_SLOP_ADJECTIVES` as fits part-of-speech:
- `methodology` → `_SLOP_NOUNS`
- `aforementioned`, `subsequent` → `_SLOP_ADJECTIVES`

**Over-explanation single words** (issue rule 8, word subset) — add to `_SLOP_HEDGE` (existing advice "Cut '{word}' — start the sentence directly or show the connection without announcing it." fits these well):
- `obviously`, `clearly`, `naturally`, `self-evidently`

## What gets skipped (and why)

| Issue rule | Reason |
|---|---|
| Qualifier words (very, quite, rather, …) | High false-positive risk on legitimate prose; routing through `_SLOP_HEDGE` advice ("Cut … or show the connection") doesn't fit "very". Worth a deliberate new rule, not a list-append. |
| Long sentences (40 words) | `ExtremeSentenceRule` already covers this at 140 words; changing the threshold would touch the maintainer's calibration. |
| Passive voice | Two-tier detection with 55 participles is a real new rule; can't be a list-append. |
| Exclamation density | Needs a new Rule class paralleling `EmDashDensityRule` — out of scope for "minimum change". |
| Emoji in prose | New Rule class. |
| Narrative-poetic headings | New Rule class with markdown-heading awareness. |

## Files touched

- `src/slop_guard/rules/sentence/slop_phrase.py` — append ~38 strings to one tuple
- `src/slop_guard/rules/word/slop_word.py` — append ~17 strings across four tuples

No catalog change, no default.jsonl change, no new files, no rule registration.

## Verification

1. `make check` — must pass formatting, lint, type, and coverage gates (per `CLAUDE.md`).
2. `uv run pytest tests/` — existing tests for `slop_phrase` and `slop_word` should still pass (they fixture-test specific phrases, and we're only adding, never removing).
3. Smoke check: `uv run sg -v -` with a paragraph containing several new phrases (e.g., "It is obvious that we need to think outside the box and move the needle on the methodology, due to the fact that the end result was completely destroyed.") should report multiple violations citing the new entries.
4. Run `slop-guard` MCP tools (or `sg`) on the README per the repo's own writing-quality rule in `CLAUDE.md`.

## Git workflow (per CLAUDE.md)

1. Add the user's GitHub fork as a remote: `git remote add mgill git@github.com:mgill/slop-guard.git` (need to confirm exact fork URL — user said "mgill on github" but the username may differ).
2. Create a worktree on a new branch off `main`.
3. Make the data-tuple additions.
4. Run `make check` and the smoke test.
5. Commit with no AI-authorship attribution.
6. Push to the user's fork (`mgill` remote).
7. Open a PR against `eric-tramel/slop-guard` using the description template from `CLAUDE.md` (Description / Why / Usage / Verification / Issues, with `Closes #9` partial — note in PR that this addresses the additive subset of issue #9 and explicitly calls out the deferred new-Rule families).
