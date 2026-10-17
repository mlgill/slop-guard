# Writing profiles

Select a profile for the audience and purpose of a draft:

| Profile | Intended use | Pattern penalty | Repeated phrase threshold |
| --- | --- | --- | --- |
| `casual` | Brief, warm personal writing with natural contractions | -1 per match | Three occurrences of 4–8 words |
| `professional-email` | Clear purpose, request, or next step in warm professional language | -2 per match | Three occurrences of 4–8 words |
| `leadership-update` | Outcomes, status, impact, evidence, and relevant decisions | -2 per match | Two occurrences of 6–8 words |

Each profile combines five existing rules with the substantial-prose rule:
setup/resolution, phrase reuse, verbose phrases, redundant pairs, and clichés.
The new phrase inventory has no duplicates of the existing cliché inventory.
The JSONL assets explicitly specify penalties, thresholds, caps, and review criteria.
Their `{"prose_only": true}` header excludes Markdown and HTML code from all
profile rules, word counts, and fitting. Saved configurations retain this header.
The existing `default`, `writing_quality`, and `all` presets retain their rule sets.

The profiles flag selected stock phrases from ten prose words onward. At fifty
prose words they also return `review_requirements`: contextual questions for the
writing agent to assess. Shorter passages have no semantic requirement in the
payload. The existing analyzer exemption below ten words still applies.
A score of 100 means no configured pattern penalty; it does not certify good
writing or complete semantic review. Review findings against the draft's purpose
before revising, including quoted examples and intentional repetition.

All profiles preserve source facts, numbers, citations, links, and uncertainty.
Their contextual guidance favors direct, connected prose and familiar words while
retaining useful technical terms. Grammar, punctuation, dates, genuine questions,
first-person updates, and useful headings or lists have no blanket bans.
Context-sensitive technical vocabulary requires judgment.

The leadership profile allows methods, metrics, bold topic titles, and nested
bullets when they help a broad technical audience. It qualifies preliminary
results and checks audience authorization for personal attribution or sensitive
business details. This profile assesses writing; it does not validate science.

```bash
sg --preset casual -v draft.md
sg --preset professional-email --json email.md
sg --preset leadership-update status.md
slop-guard --preset casual --require-absolute-paths
```

Both MCP tools accept an optional `profile` argument with these three names or
the existing preset names. Omit it to use the startup preset. Selecting a profile
affects that call only. The returned `profile` identifies the choice, or `custom`
for startup `--config` rules. Unknown names fail validation. Plugin launchers
should pass `--require-absolute-paths` and send absolute paths to `check_slop_file`
so the server's working directory cannot select the wrong file.

## Optional report hook

`sg-hook --preset casual` reads a JSON Stop event from stdin. It requires
`hook_event_name: "Stop"`, `stop_hook_active: false`, and a nonempty string
`last_assistant_message`. It ignores transcript paths and unsupported events.
When patterns match, it returns a compact `systemMessage` with the score, count,
and rule names. It does not repeat source text, block completion, or request a
retry. It exits zero for handled events and no-ops, or one for errors; it never
uses the blocking exit status two. A hook does not perform semantic review.

Hook installation is optional and belongs to the client's plugin configuration.
The package does not install hooks or change client settings.

These presets were checked against synthetic positive and negative examples
based on stated writing preferences. No private writing corpus was used.
See [upstream attribution](https://github.com/mlgill/slop-guard/blob/main/THIRD_PARTY_NOTICES.md)
for the source revisions adapted here.
