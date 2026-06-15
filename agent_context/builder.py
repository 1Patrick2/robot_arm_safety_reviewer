from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from runtime_db.episode_ingest import build_artifact_records as _build_artifact_records
from runtime_db.repository import RuntimeMetricsRepository
from runtime_db.schema import init_runtime_db

from .models import AgentContext, AgentContextArtifact, AgentContextStep


def _normalise_step(step: dict[str, Any]) -> dict[str, Any]:
    """Convert a step dict (from DB or episode) into a standard form with
    a ``safety_result`` sub-dict.

    DB rows from ``RuntimeMetricsRepository.get_steps()`` return flat columns
    (``decision``, ``risk_level``, ``safety_result_json``, ...) rather than a
    nested ``safety_result``.  This helper bridges the gap.
    """
    sr: dict[str, Any] | None = step.get("safety_result")
    if isinstance(sr, dict) and sr:
        return step  # already normalised (episode-dir path)

    step = dict(step)  # shallow copy

    # 1. Parse stored JSON if available
    raw = step.get("safety_result_json")
    if isinstance(raw, str) and raw.strip():
        try:
            sr = json.loads(raw)
            if isinstance(sr, dict):
                step["safety_result"] = sr
                return step
        except (json.JSONDecodeError, ValueError):
            pass

    # 2. Fall back to top-level columns
    step["safety_result"] = {
        "decision": step.get("decision"),
        "risk_level": step.get("risk_level"),
        "min_clearance": step.get("min_clearance"),
        "closest_robot_link": step.get("closest_robot_link"),
        "closest_obstacle": step.get("closest_obstacle"),
        "worst_step": step.get("worst_step"),
    }
    return step


def _select_critical_steps(
    steps: list[dict[str, Any]],
    *,
    max_steps: int = 10,
) -> list[AgentContextStep]:
    """Select critical steps deterministically.

    Priority order:
    1. All reject steps.
    2. All manual_review steps.
    3. The min-clearance step.
    4. Remaining slots filled with approve steps (lowest clearance first).
    """
    # Normalise every step first (handles both DB rows and episode-dir dicts).
    steps = [_normalise_step(s) for s in steps]

    rejected: list[dict] = []
    manual: list[dict] = []
    approved: list[dict] = []

    for s in steps:
        decision = (s.get("safety_result") or {}).get("decision")
        if decision == "reject":
            rejected.append(s)
        elif decision == "manual_review":
            manual.append(s)
        else:
            approved.append(s)

    # Sort each group: lower clearance first, then lower step_index
    # Use is-not-None checks so that 0.0 (contact boundary) is kept as-is
    # and None (unknown) is sorted last.
    def _clearance(s: dict) -> float:
        c = (s.get("safety_result") or {}).get("min_clearance")
        return float(c) if c is not None else float("inf")

    def _index(s: dict) -> int:
        idx = s.get("step_index")
        return int(idx) if idx is not None else 999999

    rejected.sort(key=lambda s: (_clearance(s), _index(s)))
    manual.sort(key=lambda s: (_clearance(s), _index(s)))
    approved.sort(key=lambda s: (_clearance(s), _index(s)))

    selected: list[dict] = []
    seen: set[int | str] = set()

    def add(s: dict) -> None:
        idx = s.get("step_index") if s.get("step_index") is not None else s.get("step_id")
        if idx is not None and idx not in seen:
            seen.add(idx)
            selected.append(s)

    # 1. All reject
    for s in rejected:
        add(s)

    # 2. All manual_review
    for s in manual:
        add(s)

    # 3. Min-clearance step (may already be included)
    if approved and len(selected) < max_steps:
        add(approved[0])

    # 4. Fill remaining with approve (lowest clearance)
    for s in approved:
        if len(selected) >= max_steps:
            break
        add(s)

    result: list[AgentContextStep] = []
    for s in selected:
        sr = s.get("safety_result") or {}
        result.append(
            AgentContextStep(
                step_index=s.get("step_index"),
                step_id=s.get("step_id"),
                decision=sr.get("decision"),
                risk_level=sr.get("risk_level"),
                executed=bool(s.get("executed")),
                blocked_reason=s.get("blocked_reason"),
                min_clearance=sr.get("min_clearance"),
                closest_robot_link=sr.get("closest_robot_link"),
                closest_obstacle=sr.get("closest_obstacle"),
                backend_worst_step=sr.get("worst_step"),
                proposed_action=s.get("proposed_action", {}),
                safety_result=sr,
            )
        )
    return result


def _read_metadata_json(run: dict) -> dict[str, Any]:
    """Parse the stored metadata_json from a DB run record."""
    raw = run.get("metadata_json")
    if isinstance(raw, str) and raw.strip():
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            pass
    if isinstance(raw, dict):
        return raw
    return {}


def build_agent_context_from_db(
    db_path: Path,
    episode_id: str,
    *,
    max_steps: int = 10,
) -> AgentContext:
    """Build an AgentContext from a runtime_metrics.db query.

    Uses the repository layer — never reads the database directly.
    """
    init_runtime_db(db_path)
    repo = RuntimeMetricsRepository(db_path)

    run = repo.get_run(episode_id)
    if run is None:
        raise KeyError(f"episode not found in metrics database: {episode_id}")

    db_steps = repo.get_steps(episode_id)
    meta = _read_metadata_json(run)

    # Build artifact records from the stored artifact paths
    artifacts: list[AgentContextArtifact] = []
    ep_dir_str = run.get("episode_dir")
    if ep_dir_str:
        ep_dir = Path(ep_dir_str)
        if ep_dir.exists():
            for rec in _build_artifact_records(ep_dir):
                artifacts.append(
                    AgentContextArtifact(
                        kind=rec["kind"],
                        path=rec["path"],
                        description=rec.get("description"),
                    )
                )

    critical_steps = _select_critical_steps(db_steps, max_steps=max_steps)

    return AgentContext(
        episode_id=str(run.get("episode_id", episode_id)),
        sequence_id=run.get("sequence_id"),
        backend=run.get("backend"),
        device=run.get("device"),
        run_mode=meta.get("run_mode"),
        total_steps=run.get("total_steps") or 0,
        approved_steps=run.get("approved_steps") or 0,
        executed_steps=run.get("executed_steps") or 0,
        blocked_steps=run.get("blocked_steps") or 0,
        rejected_steps=run.get("rejected_steps") or 0,
        manual_review_steps=run.get("manual_review_steps") or 0,
        min_clearance=run.get("min_clearance"),
        worst_sequence_step_index=run.get("worst_sequence_step_index"),
        backend_worst_step=run.get("backend_worst_step"),
        closest_robot_link=run.get("closest_robot_link"),
        closest_obstacle=run.get("closest_obstacle"),
        critical_steps=tuple(critical_steps),
        artifacts=tuple(artifacts),
    )
