"""Check substantial prose and request contextual review.

Objective: Find configured stock phrases once prose reaches its phrase threshold.
Return pending semantic criteria at a separate substantial-prose threshold,
even when no phrase matches.
Code examples are masked before counting words or locating phrases.

Example Rule Violations:
    - "Bottom line: this is a game-changing solution."
      Announces the conclusion and praises the work without evidence.

Example Non-Violations:
    - "The report that I sent today includes the artifact provenance."
      Uses ordinary grammar and contextually useful technical terms.

Severity: Configurable per phrase. Semantic review does not change the score.

Adapted from Eric Tramel's MIT-licensed substantial prose rule in PR 125;
see THIRD_PARTY_NOTICES.md for the source revision and scope of adaptation.
"""

import re
from dataclasses import dataclass

from slop_guard.document import AnalysisDocument, context_around, word_count
from slop_guard.models import (
    ReviewCriterionPayload,
    ReviewRequirement,
    RuleResult,
    Violation,
)
from slop_guard.rules.base import Rule, RuleConfig, RuleLevel
from slop_guard.rules.prose import prose_text


@dataclass
class SubstantialProseStyleRuleConfig(RuleConfig):
    """Explicit phrase checks and semantic criteria for a writing profile.

    Attributes:
        min_words: Minimum prose words before semantic review is requested.
        phrase_min_words: Minimum prose words before phrase matching runs.
        penalty: Negative score contribution per recorded phrase.
        record_cap: Maximum recorded findings, with all matches counted.
        context_window_chars: Width of surrounding source context.
        phrases: Literal stock phrases to flag, matched at word boundaries.
        semantic_criteria: Contextual questions for the writing agent to assess.
    """

    min_words: int
    phrase_min_words: int
    penalty: int
    record_cap: int
    context_window_chars: int
    phrases: list[str]
    semantic_criteria: list[ReviewCriterionPayload]

    def __post_init__(self) -> None:
        """Reject missing, malformed, or ineffective profile configuration."""
        for key in (
            "min_words",
            "phrase_min_words",
            "record_cap",
            "context_window_chars",
        ):
            value = getattr(self, key)
            if type(value) is not int or value < 1:
                raise ValueError(f"{key} must be a positive integer")
        if type(self.penalty) is not int or self.penalty > 0:
            raise ValueError("penalty must be a non-positive integer")
        if (
            not isinstance(self.phrases, list)
            or not self.phrases
            or any(
                not isinstance(item, str) or not item.strip() for item in self.phrases
            )
        ):
            raise ValueError("phrases must be a nonempty list of nonempty strings")
        if not isinstance(self.semantic_criteria, list) or not self.semantic_criteria:
            raise ValueError("semantic_criteria must be a nonempty list")
        for item in self.semantic_criteria:
            if (
                not isinstance(item, dict)
                or set(item) != {"key", "instruction"}
                or any(
                    not isinstance(value, str) or not value.strip()
                    for value in item.values()
                )
            ):
                raise ValueError(
                    "Each semantic criterion requires a key and instruction"
                )


class SubstantialProseStyleRule(Rule[SubstantialProseStyleRuleConfig]):
    """Flag stock phrases and supply pending contextual writing guidance."""

    name = "substantial_prose_style"
    count_key = "substantial_prose_style"
    category = "writing_quality"
    level = RuleLevel.PASSAGE

    def __init__(self, config: SubstantialProseStyleRuleConfig) -> None:
        """Compile configured phrases once for this rule instance."""
        super().__init__(config)
        self._pattern = re.compile(
            r"(?<!\w)(?:"
            + "|".join(
                re.escape(phrase)
                for phrase in sorted(
                    config.phrases, key=lambda value: len(value), reverse=True
                )
            )
            + r")(?!\w)",
            re.I,
        )

    def example_violations(self) -> list[str]:
        """Return a configured phrase in a passage above the threshold."""
        return [
            self.config.phrases[0]
            + " The report includes the measured result." * self.config.min_words
        ]

    def example_non_violations(self) -> list[str]:
        """Return ordinary prose using natural grammar and technical terms."""
        return [
            "I checked the artifact provenance today; the records that we need are available."
        ]

    def forward(self, document: AnalysisDocument) -> RuleResult:
        """Run phrase checks and require semantic review for substantial prose."""
        text = prose_text(document)
        words = word_count(text)
        if words < min(self.config.min_words, self.config.phrase_min_words):
            return RuleResult()
        matches = (
            list(self._pattern.finditer(text))
            if words >= self.config.phrase_min_words
            else []
        )
        return RuleResult(
            violations=[
                Violation(
                    rule=self.name,
                    match=match[0],
                    context=context_around(
                        document.text,
                        match.start(),
                        match.end(),
                        self.config.context_window_chars,
                    ),
                    penalty=self.config.penalty,
                    start=match.start(),
                    end=match.end(),
                )
                for match in matches[: self.config.record_cap]
            ],
            advice=[
                "Review matched stock phrases in context; state the useful point directly."
            ]
            if matches
            else [],
            count_deltas={self.count_key: len(matches)},
            review_requirements=[
                ReviewRequirement(
                    rule=self.name,
                    reason="Pending contextual review: the score measures configured patterns, not whether the writing meets these criteria.",
                    criteria=tuple(self.config.semantic_criteria),
                )
            ]
            if words >= self.config.min_words
            else [],
        )
