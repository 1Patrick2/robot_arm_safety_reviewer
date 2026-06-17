from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RootCauseHypothesis:
    """A single root-cause hypothesis in a diagnostic analysis.

    Attributes:
        hypothesis: Natural-language description of the hypothesis.
        evidence_refs: Dot-path references to evidence that supports
            this hypothesis.
        confidence: ``"low"``, ``"medium"``, or ``"high"``.
    """

    hypothesis: str
    evidence_refs: tuple[str, ...]
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "evidence_refs": list(self.evidence_refs),
            "confidence": self.confidence,
        }


@dataclass(frozen=True)
class DiagnosticAnalysis:
    """Structured output of a diagnostic analyst run.

    Attributes:
        schema_version: Always ``"llm_diagnostic_analysis.v1"``.
        case_id: The case or sequence identifier being analysed.
        episode_id: The episode identifier for the runtime run.
        analysis_mode: ``"fake"`` (deterministic) or future provider name.
        deterministic_outcome: A flat dict of the actual safety outcome
            (same fields as ``build_actual_summary()``).
        risk_summary: A single-sentence summary of the safety risk.
        root_cause_hypotheses: Zero or more evidence-supported hypotheses.
        evidence_used: Artifact kinds that were read during analysis.
        uncertainties: What the analysis does not know or cannot conclude.
        prohibited_actions_detected: Any prohibited statements found in
            the analysis output (empty for fake analyst).
    """

    schema_version: str = "llm_diagnostic_analysis.v1"
    case_id: str | None = None
    episode_id: str | None = None
    analysis_mode: str = "fake"
    deterministic_outcome: dict[str, Any] = field(default_factory=dict)
    risk_summary: str = ""
    root_cause_hypotheses: tuple[RootCauseHypothesis, ...] = ()
    evidence_used: tuple[str, ...] = ()
    uncertainties: tuple[str, ...] = ()
    prohibited_actions_detected: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "case_id": self.case_id,
            "episode_id": self.episode_id,
            "analysis_mode": self.analysis_mode,
            "deterministic_outcome": self.deterministic_outcome,
            "risk_summary": self.risk_summary,
            "root_cause_hypotheses": [h.to_dict() for h in self.root_cause_hypotheses],
            "evidence_used": list(self.evidence_used),
            "uncertainties": list(self.uncertainties),
            "prohibited_actions_detected": list(self.prohibited_actions_detected),
        }
