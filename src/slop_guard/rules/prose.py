"""Run audience profiles on prose while preserving original source offsets."""

import re
from dataclasses import replace
from pathlib import Path

from slop_guard.config import DEFAULT_HYPERPARAMETERS
from slop_guard.document import AnalysisDocument
from slop_guard.models import AnalysisState
from slop_guard.scoring import serialize_violations

from .base import Label
from .pipeline import Pipeline

_HTML_CODE_RE = re.compile(r"<(code|pre)\b[^>]*>.*?</\1>", re.I | re.S)


def prose_text(document: AnalysisDocument) -> str:
    """Mask Markdown and HTML code without moving any source character."""
    return _HTML_CODE_RE.sub(
        lambda match: "".join("\n" if char == "\n" else " " for char in match[0]),
        document.text_with_markdown_code_masked,
    )


class ProsePipeline(Pipeline):
    """Keep existing rules from inspecting code in opt-in audience profiles."""

    def to_jsonl(self, path: str | Path) -> None:
        """Preserve the explicit prose projection when fitting or exporting rules."""
        super().to_jsonl(path)
        target = Path(path)
        target.write_text(
            '{"prose_only": true}\n' + target.read_text(encoding="utf-8"),
            encoding="utf-8",
        )

    def forward(self, document: AnalysisDocument) -> AnalysisState:
        """Resolve all findings against masked prose before restoring source text."""
        masked = prose_text(document)
        state = super().forward(AnalysisDocument.from_text(masked))
        # Older rules infer spans from their match text. Resolve against the
        # masked view so an identical example in code cannot steal the location.
        resolved = serialize_violations(
            state.violations, masked, DEFAULT_HYPERPARAMETERS.context_window_chars
        )
        return replace(
            state,
            violations=tuple(
                replace(violation, start=row["start"], end=row["end"])
                for violation, row in zip(state.violations, resolved, strict=True)
            ),
        )

    def prepare_document(self, document: AnalysisDocument) -> AnalysisDocument:
        """Exclude code from both the global word threshold and score density."""
        return AnalysisDocument.from_text(prose_text(document))

    def fit(
        self,
        samples: list[str],
        labels: list[Label] | None = None,
        *,
        calibrate_contrastive: bool = True,
    ) -> "ProsePipeline":
        """Fit rules and contrastive penalties against the same prose projection."""
        self._validate_samples(samples, labels)
        masked = [prose_text(AnalysisDocument.from_text(text)) for text in samples]
        super().fit(masked, labels, calibrate_contrastive=calibrate_contrastive)
        return self

    def _validate_samples(self, samples: list[str], labels: list[Label] | None) -> None:
        """Use existing rule validation before creating document projections."""
        for rule in self.rules:
            rule._validate_fit_inputs(samples, labels)
