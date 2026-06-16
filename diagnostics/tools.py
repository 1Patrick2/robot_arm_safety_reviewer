from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_diagnostic_context(path: str | Path) -> dict[str, Any]:
    """Load a diagnostic_context.json file and return its contents."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"diagnostic context not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def get_episode_summary(bundle: dict[str, Any]) -> dict[str, Any]:
    """Extract a high-level summary from a diagnostic context bundle."""
    return {
        "episode_id": bundle.get("episode_id"),
        "sequence_id": bundle.get("sequence_id"),
        "backend": bundle.get("backend"),
        "total_steps": bundle.get("total_steps", 0),
        "approved": bundle.get("approved_steps", 0),
        "executed": bundle.get("executed_steps", 0),
        "blocked": bundle.get("blocked_steps", 0),
        "rejected": bundle.get("rejected_steps", 0),
        "manual_review": bundle.get("manual_review_steps", 0),
        "min_clearance": bundle.get("min_clearance"),
        "worst_sequence_step_index": bundle.get("worst_sequence_step_index"),
    }


def list_critical_steps(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the list of critical steps from the context."""
    return list(bundle.get("critical_steps", []))


def get_worst_step(bundle: dict[str, Any]) -> dict[str, Any] | None:
    """Return the critical step with the lowest min_clearance, or None."""
    steps = list_critical_steps(bundle)
    if not steps:
        return None
    return min(
        steps,
        key=lambda s: s.get("min_clearance") if s.get("min_clearance") is not None else float("inf"),
    )


def get_artifact_index(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the list of artifact references from the context."""
    return list(bundle.get("artifacts", []))
