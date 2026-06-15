from __future__ import annotations

from pathlib import Path
from typing import Any

from runtime_db.repository import RuntimeMetricsRepository
from runtime_db.schema import init_runtime_db


def _safe_float(val: Any) -> float | None:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def build_run_record(episode_dir: Path) -> dict[str, Any]:
    """Extract a run-level dict from *episode_dir*."""
    episode_dir = Path(episode_dir)
    meta_path = episode_dir / "metadata.json"
    if not meta_path.exists():
        raise FileNotFoundError(f"metadata.json not found: {meta_path}")
    import json  # noqa: PLC0415
    meta: dict[str, Any] = json.loads(meta_path.read_text(encoding="utf-8"))

    steps_path = episode_dir / "steps.jsonl"
    steps: list[dict[str, Any]] = []
    if steps_path.exists():
        with steps_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    steps.append(json.loads(line))

    approved = sum(1 for s in steps if (s.get("safety_result") or {}).get("decision") == "approve")
    executed = sum(1 for s in steps if s.get("executed"))
    blocked = sum(1 for s in steps if s.get("blocked_reason") is not None)
    rejected = sum(1 for s in steps if (s.get("safety_result") or {}).get("decision") == "reject")
    manual_review = sum(1 for s in steps if (s.get("safety_result") or {}).get("decision") == "manual_review")

    # aggregate clearance stats across steps
    clearances = [_safe_float((s.get("safety_result") or {}).get("min_clearance")) for s in steps]
    valid_clearances = [c for c in clearances if c is not None]
    min_clearance = min(valid_clearances) if valid_clearances else None

    worst_step: int | None = None
    closest_link: str | None = None
    closest_obs: str | None = None
    # Find the worst step (lowest clearance) for overview
    if valid_clearances:
        worst_idx = clearances.index(min_clearance)
        sr = steps[worst_idx].get("safety_result", {})
        worst_step = sr.get("worst_step")
        closest_link = sr.get("closest_robot_link")
        closest_obs = sr.get("closest_obstacle")

    summary_path = episode_dir / "episode_summary.md"
    clearance_path = episode_dir / "clearance_curve.png"
    trajectory_path = episode_dir / "trajectory_overview.png"

    return {
        "episode_id": meta.get("episode_id", episode_dir.name),
        "sequence_id": meta.get("sequence_id"),
        "backend": meta.get("backend"),
        "device": meta.get("device"),
        "robot": meta.get("robot"),
        "action_source": meta.get("action_source"),
        "scene_provider": meta.get("scene_provider"),
        "created_at": meta.get("created_at"),
        "episode_dir": str(episode_dir),
        "total_steps": len(steps),
        "approved_steps": approved,
        "executed_steps": executed,
        "blocked_steps": blocked,
        "rejected_steps": rejected,
        "manual_review_steps": manual_review,
        "min_clearance": min_clearance,
        "worst_step": worst_step,
        "closest_robot_link": closest_link,
        "closest_obstacle": closest_obs,
        "summary_path": str(summary_path) if summary_path.exists() else None,
        "clearance_curve_path": str(clearance_path) if clearance_path.exists() else None,
        "trajectory_overview_path": str(trajectory_path) if trajectory_path.exists() else None,
        "metadata_json": meta,
    }


def build_step_records(episode_dir: Path) -> list[dict[str, Any]]:
    """Extract step-level dicts from *episode_dir/steps.jsonl*."""
    episode_dir = Path(episode_dir)
    steps_path = episode_dir / "steps.jsonl"
    if not steps_path.exists():
        return []
    import json  # noqa: PLC0415
    steps: list[dict[str, Any]] = []
    with steps_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                steps.append(json.loads(line))
    return steps


def build_artifact_records(episode_dir: Path) -> list[dict[str, Any]]:
    """Enumerate visual artifacts present in *episode_dir*."""
    episode_dir = Path(episode_dir)
    candidates = [
        ("episode_summary", "episode_summary.md", "Episode summary markdown"),
        ("clearance_curve", "clearance_curve.png", "Clearance curve PNG"),
        ("trajectory_overview", "trajectory_overview.png", "Trajectory overview PNG"),
    ]
    records: list[dict[str, Any]] = []
    for kind, filename, desc in candidates:
        p = episode_dir / filename
        if p.exists():
            records.append({"kind": kind, "path": str(p), "description": desc})
    return records


def ingest_episode(db_path: Path, episode_dir: Path) -> dict[str, Any]:
    """Ingest an episode directory into the metrics database.

    Returns a summary dict with episode_id and counts.
    """
    init_runtime_db(db_path)
    repo = RuntimeMetricsRepository(db_path)

    run_record = build_run_record(episode_dir)
    step_records = build_step_records(episode_dir)
    artifact_records = build_artifact_records(episode_dir)

    repo.upsert_run(run_record)
    repo.replace_steps(run_record["episode_id"], step_records)
    repo.replace_artifacts(run_record["episode_id"], artifact_records)

    return {
        "episode_id": run_record["episode_id"],
        "total_steps": run_record["total_steps"],
        "approved_steps": run_record["approved_steps"],
        "executed_steps": run_record["executed_steps"],
        "blocked_steps": run_record["blocked_steps"],
        "rejected_steps": run_record["rejected_steps"],
        "manual_review_steps": run_record["manual_review_steps"],
        "min_clearance": run_record["min_clearance"],
        "artifact_count": len(artifact_records),
    }
