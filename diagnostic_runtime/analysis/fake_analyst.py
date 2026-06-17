from __future__ import annotations

from typing import Any

from .evidence_refs import build_basic_evidence_refs
from .models import DiagnosticAnalysis, RootCauseHypothesis


def run_fake_diagnostic_analyst(
    *,
    context: dict[str, Any],
    manifest: dict[str, Any],
    deterministic_report: str | None = None,
) -> DiagnosticAnalysis:
    """Deterministic fake diagnostic analyst.

    Produces a structured ``DiagnosticAnalysis`` by reading the provided
    diagnostic evidence directly — no external API or LLM involved.
    """
    summary = _extract_summary(context)

    # --- final status ---
    rejected = summary.get("rejected_steps", 0) or 0
    manual_review = summary.get("manual_review_steps", 0) or 0
    if rejected > 0:
        final_status = "reject"
    elif manual_review > 0:
        final_status = "manual_review"
    else:
        final_status = "approve"

    # --- risk_summary ---
    if final_status == "reject":
        risk_summary = (
            "The sequence contains at least one rejected step "
            "based on deterministic safety evidence."
        )
    elif final_status == "manual_review":
        risk_summary = (
            "The sequence contains a manual-review condition "
            "based on deterministic safety evidence."
        )
    else:
        risk_summary = (
            "The sequence is approved by the deterministic safety runtime."
        )

    # --- root_cause_hypotheses ---
    hypotheses: list[RootCauseHypothesis] = []
    closest_obs = summary.get("closest_obstacle")
    min_clear = summary.get("min_clearance")
    if closest_obs is not None and min_clear is not None:
        refs = [f"summary.{k}" for k in ("min_clearance", "closest_obstacle")]
        if summary.get("closest_robot_link") is not None:
            refs.append("summary.closest_robot_link")
        refs.append("evidence_groups.geometry")
        hypotheses.append(RootCauseHypothesis(
            hypothesis=f"The minimum clearance is associated with obstacle {closest_obs}.",
            evidence_refs=tuple(refs),
            confidence="medium",
        ))
    else:
        hypotheses.append(RootCauseHypothesis(
            hypothesis="No geometry-specific root cause can be identified "
                       "from the available evidence.",
            evidence_refs=("evidence_groups.geometry",),
            confidence="low",
        ))

    # --- evidence_used ---
    available_kinds = _available_kinds(manifest)
    evidence_used = [k for k in (
        "diagnostic_context_json",
        "deterministic_report",
        "diagnostic_runtime_trace",
        "trajectory_overview_data",
        "evidence_manifest",
    ) if k in available_kinds]

    # --- uncertainties ---
    uncertainties = [
        "The analysis is based on structured diagnostic evidence, "
        "not raw image understanding.",
    ]
    available_groups = _available_groups(manifest)
    if "geometry" not in available_groups:
        uncertainties.append(
            "Geometry evidence is unavailable or incomplete."
        )

    return DiagnosticAnalysis(
        case_id=context.get("sequence_id") or context.get("case_id"),
        episode_id=context.get("episode_id"),
        deterministic_outcome={
            "final_status": final_status,
            "total_steps": summary.get("total_steps"),
            "approved_steps": summary.get("approved_steps"),
            "manual_review_steps": summary.get("manual_review_steps"),
            "rejected_steps": summary.get("rejected_steps"),
            "min_clearance": summary.get("min_clearance"),
        },
        risk_summary=risk_summary,
        root_cause_hypotheses=tuple(hypotheses),
        evidence_used=tuple(evidence_used),
        uncertainties=tuple(uncertainties),
        prohibited_actions_detected=(),
    )


def _extract_summary(context: dict[str, Any]) -> dict[str, Any]:
    """Extract a flat summary dict from a diagnostic context."""
    fields = (
        "total_steps", "approved_steps", "executed_steps", "blocked_steps",
        "rejected_steps", "manual_review_steps", "min_clearance",
        "closest_robot_link", "closest_obstacle", "worst_sequence_step_index",
        "backend_worst_step",
    )
    return {f: context.get(f) for f in fields}


def _available_kinds(manifest: dict[str, Any]) -> set[str]:
    from .evidence_refs import collect_available_evidence_kinds
    return collect_available_evidence_kinds(manifest)


def _available_groups(manifest: dict[str, Any]) -> set[str]:
    from .evidence_refs import collect_available_evidence_groups
    return collect_available_evidence_groups(manifest)
