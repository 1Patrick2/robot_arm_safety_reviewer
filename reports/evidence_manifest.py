from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_evidence_manifest(
    *,
    context_path: Path,
    deterministic_report_path: Path | None = None,
    agent_report_path: Path | None = None,
    trace_path: Path | None = None,
) -> dict[str, Any]:
    """Build a structured evidence manifest for a diagnostic run.

    The manifest indexes all evidence files produced by a diagnostic
    pipeline run (context, reports, visual artifacts, trace, etc.).

    Args:
        context_path: Path to an existing ``diagnostic_context.json``.
        deterministic_report_path: Path to the deterministic diagnostic report.
        agent_report_path: Path to the agent-generated report (optional).
        trace_path: Path to the diagnostic runtime trace JSON (optional).

    Returns:
        A dict conforming to ``evidence_manifest.v1`` schema.
    """
    context_path = Path(context_path)
    if not context_path.exists():
        raise FileNotFoundError(f"context not found: {context_path}")

    try:
        context = json.loads(context_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid diagnostic context JSON: {context_path}") from exc

    if not isinstance(context, dict):
        raise ValueError(
            f"diagnostic context must be a JSON object, got {type(context).__name__}"
        )

    episode_id = context.get("episode_id", "unknown")

    # -- collect artifacts ---------------------------------------------------
    artifacts: list[dict[str, Any]] = []

    def add(kind: str, path: str | Path, source: str) -> None:
        artifacts.append({
            "kind": kind,
            "path": str(path),
            "exists": Path(path).exists(),
            "source": source,
        })

    # 1. context JSON
    add("diagnostic_context_json", context_path, "diagnostic_runtime.context")

    # 2. context Markdown (same dir, diagnostic_context.md)
    context_md = context_path.parent / "diagnostic_context.md"
    if context_md.exists():
        add("diagnostic_context_markdown", context_md, "diagnostic_runtime.context")

    # 3. artifacts from context JSON
    for art in context.get("artifacts", []):
        art_path = art.get("path", "")
        if art_path:
            add(art.get("kind", "unknown"), art_path, "diagnostic_context")

    # 4. deterministic report
    if deterministic_report_path is not None:
        add("deterministic_report", deterministic_report_path, "diagnostic_runtime.report")

    # 5. agent report
    if agent_report_path is not None:
        add("diagnostic_agent_report", agent_report_path, "diagnostic_runtime.agent")

    # 6. runtime trace
    if trace_path is not None:
        add("diagnostic_runtime_trace", trace_path, "diagnostic_runtime.runtime")

    # -- compute checks ------------------------------------------------------
    def _artifact_exists(kind: str) -> bool:
        return any(a["kind"] == kind and a["exists"] for a in artifacts)

    def _any_existing(kinds: set[str]) -> bool:
        return any(a["kind"] in kinds and a["exists"] for a in artifacts)

    has_guardrail_violations = False
    if trace_path is not None:
        tp = Path(trace_path)
        if tp.exists():
            try:
                trace_data = json.loads(tp.read_text(encoding="utf-8"))
                if trace_data.get("has_violations"):
                    has_guardrail_violations = True
            except (OSError, json.JSONDecodeError, AttributeError):
                pass

    checks: dict[str, bool] = {
        "has_visual_evidence": _any_existing({"episode_summary", "clearance_curve", "trajectory_overview"}),
        "has_structured_visual_data": _any_existing({"trajectory_overview_data", "clearance_curve_data"}),
        "has_diagnostic_context": _artifact_exists("diagnostic_context_json"),
        "has_diagnostic_report": _artifact_exists("deterministic_report"),
        "has_trace": _artifact_exists("diagnostic_runtime_trace"),
        "has_agent_report": _artifact_exists("diagnostic_agent_report"),
        "has_guardrail_violations": has_guardrail_violations,
    }

    # -- summary -------------------------------------------------------------
    summary: dict[str, Any] = {
        "total_steps": context.get("total_steps"),
        "approved_steps": context.get("approved_steps"),
        "executed_steps": context.get("executed_steps"),
        "blocked_steps": context.get("blocked_steps"),
        "rejected_steps": context.get("rejected_steps"),
        "manual_review_steps": context.get("manual_review_steps"),
        "min_clearance": context.get("min_clearance"),
        "worst_sequence_step_index": context.get("worst_sequence_step_index"),
        "backend_worst_step": context.get("backend_worst_step"),
        "closest_robot_link": context.get("closest_robot_link"),
        "closest_obstacle": context.get("closest_obstacle"),
    }

    return {
        "schema_version": "evidence_manifest.v1",
        "episode_id": episode_id,
        "sequence_id": context.get("sequence_id"),
        "backend": context.get("backend"),
        "device": context.get("device"),
        "run_mode": context.get("run_mode"),
        "summary": summary,
        "artifacts": artifacts,
        "checks": checks,
    }


def write_evidence_manifest(manifest: dict[str, Any], output_path: Path) -> Path:
    """Write an evidence manifest dict to *output_path* as pretty-printed JSON."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return output_path
