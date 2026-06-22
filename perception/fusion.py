from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import SafetyObservation

_ALLOWED_DECISIONS = frozenset({"approve", "manual_review", "reject"})

_MANUAL_REVIEW_KINDS = frozenset({
    "human_in_warning_zone",
    "object_in_warning_zone",
    "object_in_danger_zone",
    "unknown_object_detected",
    "low_confidence_detection",
    "close_object_detected",
})


@dataclass(frozen=True)
class PerceptionSafetyFusionResult:
    """Result of fusing a deterministic safety decision with perception observations.

    Attributes:
        original_decision: The original deterministic decision (``"approve"``,
            ``"manual_review"``, or ``"reject"``).
        fused_decision: The perception-aware fused decision.
        original_risk_level: Original risk level, if available.
        fused_risk_level: Fused risk level, if applicable.
        triggered_observations: Only the observations that influenced the fused
            decision.
        reasons: Human-readable reasons for the fusion outcome.
        evidence_refs: Deduplicated evidence refs from triggered observations.
    """

    original_decision: str
    fused_decision: str
    original_risk_level: str | None = None
    fused_risk_level: str | None = None
    triggered_observations: tuple[SafetyObservation, ...] = ()
    reasons: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "perception_safety_fusion_result.v1",
            "original_decision": self.original_decision,
            "fused_decision": self.fused_decision,
            "original_risk_level": self.original_risk_level,
            "fused_risk_level": self.fused_risk_level,
            "triggered_observations": [
                {
                    "kind": obs.kind,
                    "object_id": obs.object_id,
                    "severity": obs.severity,
                    "frame_id": obs.frame_id,
                    "evidence_refs": list(obs.evidence_refs),
                    "metadata": dict(obs.metadata),
                }
                for obs in self.triggered_observations
            ],
            "reasons": list(self.reasons),
            "evidence_refs": list(self.evidence_refs),
        }


def fuse_safety_with_perception(
    *,
    original_decision: str,
    original_risk_level: str | None = None,
    observations: tuple[SafetyObservation, ...] = (),
) -> PerceptionSafetyFusionResult:
    """Fuse a deterministic safety decision with perception observations.

    Args:
        original_decision: One of ``"approve"``, ``"manual_review"``, ``"reject"``.
        original_risk_level: Optional original risk level.
        observations: Perception-derived ``SafetyObservation`` tuples.

    Returns:
        A ``PerceptionSafetyFusionResult`` with the fused decision.

    Raises:
        ValueError: If *original_decision* is not a valid decision.
    """
    if original_decision not in _ALLOWED_DECISIONS:
        raise ValueError(
            f"unsupported original_decision: '{original_decision}'; "
            f"expected one of {sorted(_ALLOWED_DECISIONS)}"
        )

    # Rule 1: original reject is never downgraded
    if original_decision == "reject":
        return PerceptionSafetyFusionResult(
            original_decision=original_decision,
            fused_decision="reject",
            original_risk_level=original_risk_level,
            fused_risk_level=original_risk_level,
            triggered_observations=(),
            reasons=(
                "Original deterministic safety decision is reject; "
                "perception cannot downgrade it.",
            ),
            evidence_refs=(),
        )

    triggered: list[SafetyObservation] = []
    reasons: list[str] = []

    # Rule 2: human_in_danger_zone -> reject (highest priority)
    danger_human_obs = _filter_observations(observations, kind="human_in_danger_zone")
    if danger_human_obs:
        triggered.extend(danger_human_obs)
        reasons.append(
            "Human detected in danger zone; fused decision escalated to reject."
        )
        return PerceptionSafetyFusionResult(
            original_decision=original_decision,
            fused_decision="reject",
            original_risk_level=original_risk_level,
            fused_risk_level="high",
            triggered_observations=tuple(triggered),
            reasons=tuple(reasons),
            evidence_refs=_collect_evidence_refs(tuple(triggered)),
        )

    # Rule 3: manual_review escalations
    manual_obs = _filter_observations(observations, kinds=_MANUAL_REVIEW_KINDS)
    if manual_obs:
        triggered.extend(manual_obs)
        found_kinds = {o.kind for o in manual_obs}
        reasons.append(
            f"Perception observation requires manual review: "
            f"{', '.join(sorted(found_kinds))}."
        )
        if original_decision == "approve":
            fused_risk_level = "medium"
        else:
            fused_risk_level = original_risk_level or "medium"
        return PerceptionSafetyFusionResult(
            original_decision=original_decision,
            fused_decision="manual_review",
            original_risk_level=original_risk_level,
            fused_risk_level=fused_risk_level,
            triggered_observations=tuple(triggered),
            reasons=tuple(reasons),
            evidence_refs=_collect_evidence_refs(tuple(triggered)),
        )

    # Rule 4: no trigger — keep original
    return PerceptionSafetyFusionResult(
        original_decision=original_decision,
        fused_decision=original_decision,
        original_risk_level=original_risk_level,
        fused_risk_level=original_risk_level,
        triggered_observations=(),
        reasons=("No perception observation changed the deterministic decision.",),
        evidence_refs=(),
    )


def _filter_observations(
    observations: tuple[SafetyObservation, ...],
    kind: str | None = None,
    kinds: set[str] | None = None,
) -> list[SafetyObservation]:
    """Filter observations by a single kind or a set of kinds."""
    if kind is not None:
        return [o for o in observations if o.kind == kind]
    if kinds is not None:
        return [o for o in observations if o.kind in kinds]
    return []


def _collect_evidence_refs(
    observations: tuple[SafetyObservation, ...],
) -> tuple[str, ...]:
    """Deduplicate evidence refs from observations while preserving order."""
    seen: set[str] = set()
    refs: list[str] = []
    for obs in observations:
        for ref in obs.evidence_refs:
            if ref not in seen:
                seen.add(ref)
                refs.append(ref)
    return tuple(refs)
