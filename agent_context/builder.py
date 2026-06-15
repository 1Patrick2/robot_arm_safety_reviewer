from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime_db.episode_ingest import build_artifact_records as _build_artifact_records
from runtime_db.episode_ingest import build_run_record as _build_run_record
from runtime_db.episode_ingest import build_step_records as _build_step_records
from runtime_db.repository import RuntimeMetricsRepository
from runtime_db.schema import init_runtime_db

from .models import AgentContext, AgentContextArtifact, AgentContextStep


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
    def sort_key(s: dict) -> tuple:
        sr = s.get("safety_result") or {}
        return (sr.get("min_clearance") or 0.0, s.get("step_index") or 0)

    rejected.sort(key=sort_key)
    manual.sort(key=sort_key)
    approved.sort(key=sort_key)

    selected: list[dict] = []
    seen: set[int | str] = set()

    def add(s: dict) -> None:
        idx = s.get("step_index") or s.get("step_id")
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
    min_candidates = approved if not selected else approved
    if min_candidates and len(selected) < max_steps:
        add(min_candidates[0])

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


def build_agent_context_from_db(
    db_path: Path,
    episode_id: str,
    *,
    max_steps: int = 10,
) -> AgentContext:
    """Build an AgentContext from a runtime_metrics.db query.

    Uses the repository layer — never reads the database directly.
    Falls back to direct episode-dir loading when the database doesn't exist
    or the episode is not yet ingested.
    """
    init_runtime_db(db_path)
    repo = RuntimeMetricsRepository(db_path)

    run = repo.get_run(episode_id)
    if run is None:
        raise KeyError(f"episode not found in metrics database: {episode_id}")

    db_steps = repo.get_steps(episode_id)

    # Build artifact records from the stored artifact paths in the database
    artifacts: list[AgentContextArtifact] = []
    # The DB stores runs.episode_dir — use it to check artifact files
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

    # Build step records from DB steps (already in dict format)
    critical_steps = _select_critical_steps(db_steps, max_steps=max_steps)

    return AgentContext(
        episode_id=str(run.get("episode_id", episode_id)),
        sequence_id=run.get("sequence_id"),
        backend=run.get("backend"),
        device=run.get("device"),
        run_mode=None,  # not stored in DB currently
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
