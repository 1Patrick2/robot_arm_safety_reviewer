from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_diagnostic_context(path: str | Path) -> dict[str, Any]:
    """Load a diagnostic_context.json file and return its contents.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the JSON is not a dict or cannot be parsed.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"diagnostic context not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid diagnostic context JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"diagnostic context must be a JSON object, got {type(data).__name__}")
    return data


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


def _steps_by_index(steps: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    """Build a ``{step_index: step}`` lookup."""
    result: dict[int, dict[str, Any]] = {}
    for s in steps:
        idx = s.get("step_index")
        if idx is not None:
            result[int(idx)] = s
    return result


def get_worst_step(bundle: dict[str, Any]) -> dict[str, Any] | None:
    """Return the critical step identified as the worst.

    Priority:
    1. Match ``worst_sequence_step_index`` in critical steps by ``step_index``.
    2. Fallback to the step with the lowest ``min_clearance``.
    """
    steps = list_critical_steps(bundle)
    if not steps:
        return None

    worst_idx = bundle.get("worst_sequence_step_index")
    if worst_idx is not None:
        by_idx = _steps_by_index(steps)
        matched = by_idx.get(int(worst_idx))
        if matched is not None:
            return matched

    return min(
        steps,
        key=lambda s: s.get("min_clearance") if s.get("min_clearance") is not None else float("inf"),
    )


def get_artifact_index(bundle: dict[str, Any]) -> dict[str, str]:
    """Return ``{kind: path}`` mapping of artifact references."""
    return {a.get("kind", "?"): a.get("path", "") for a in bundle.get("artifacts", [])}
