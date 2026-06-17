from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ExpectedContract:
    """A validated expected contract loaded from an ``expected_contract.v1`` JSON file."""

    case_id: str
    expected: dict[str, Any]


def load_expected_contract(path: str | Path) -> ExpectedContract:
    """Load and validate an ``expected_contract.v1`` JSON file.

    Args:
        path: Path to the expected contract JSON file.

    Returns:
        An ``ExpectedContract`` instance.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file is missing required fields or has the wrong schema version.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"expected contract not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON in expected contract: {path}") from exc

    if not isinstance(data, dict):
        raise ValueError(f"expected contract must be a JSON object, got {type(data).__name__}: {path}")

    schema_version = data.get("schema_version")
    if schema_version != "expected_contract.v1":
        raise ValueError(
            f"unsupported schema_version '{schema_version}' in {path}; "
            f"expected 'expected_contract.v1'"
        )

    case_id = data.get("case_id")
    if not case_id or not isinstance(case_id, str):
        raise ValueError(f"expected contract missing valid 'case_id' string: {path}")

    expected = data.get("expected")
    if not isinstance(expected, dict):
        raise ValueError(f"expected contract missing valid 'expected' dict: {path}")

    return ExpectedContract(case_id=case_id, expected=expected)


def build_actual_summary(context: dict[str, Any]) -> dict[str, Any]:
    """Extract an actual-safety-outcome summary from a diagnostic context dict.

    The *context* dict is the ``to_dict()`` output of an ``AgentContext``
    (i.e. the ``DiagnosticRunResult.context`` field).

    Returns:
        A flat dict with keys: ``total_steps``, ``approved_steps``,
        ``executed_steps``, ``blocked_steps``, ``rejected_steps``,
        ``manual_review_steps``, ``min_clearance``, ``closest_robot_link``,
        ``closest_obstacle``, ``worst_sequence_step_index``,
        ``backend_worst_step``, ``final_status``.
    """
    rejected = context.get("rejected_steps", 0) or 0
    manual_review = context.get("manual_review_steps", 0) or 0

    if rejected > 0:
        final_status = "reject"
    elif manual_review > 0:
        final_status = "manual_review"
    else:
        final_status = "approve"

    return {
        "total_steps": context.get("total_steps", 0),
        "approved_steps": context.get("approved_steps", 0),
        "executed_steps": context.get("executed_steps", 0),
        "blocked_steps": context.get("blocked_steps", 0),
        "rejected_steps": rejected,
        "manual_review_steps": manual_review,
        "min_clearance": context.get("min_clearance"),
        "closest_robot_link": context.get("closest_robot_link"),
        "closest_obstacle": context.get("closest_obstacle"),
        "worst_sequence_step_index": context.get("worst_sequence_step_index"),
        "backend_worst_step": context.get("backend_worst_step"),
        "final_status": final_status,
    }


def validate_expected_contract(
    *,
    expected: dict[str, Any],
    actual: dict[str, Any],
    manifest: dict[str, Any] | None = None,
) -> tuple[bool, tuple[str, ...]]:
    """Validate *actual* safety outcomes against an *expected* contract.

    Args:
        expected: The ``expected`` dict from an ``ExpectedContract``.
        actual: The dict returned by :func:`build_actual_summary`.
        manifest: Optional dict of an ``evidence_manifest.json`` (used to
            check ``required_artifacts``).

    Returns:
        A tuple ``(passed, errors)`` where *passed* is ``True`` when all
        constraints are satisfied, and *errors* is a tuple of error
        message strings.

    Supported expected fields:
        - ``total_steps``: must equal ``actual.total_steps``.
        - ``min_approved_steps``: ``actual.approved_steps >= expected``.
        - ``min_manual_review_steps``: ``actual.manual_review_steps >= expected``.
        - ``min_rejected_steps``: ``actual.rejected_steps >= expected``.
        - ``expected_final_status``: ``actual.final_status == expected``.
        - ``required_artifacts``: each kind must appear in the manifest
          with ``exists=True`` (only checked when *manifest* is provided).
    """
    errors: list[str] = []

    # total_steps
    exp_total = expected.get("total_steps")
    if exp_total is not None:
        act_total = actual.get("total_steps")
        if act_total != exp_total:
            errors.append(
                f"total_steps: expected {exp_total}, got {act_total}"
            )

    # min_approved_steps
    exp_min_approved = expected.get("min_approved_steps")
    if exp_min_approved is not None:
        act_approved = actual.get("approved_steps", 0)
        if act_approved < exp_min_approved:
            errors.append(
                f"approved_steps {act_approved} < min_approved_steps {exp_min_approved}"
            )

    # min_manual_review_steps
    exp_min_manual = expected.get("min_manual_review_steps")
    if exp_min_manual is not None:
        act_manual = actual.get("manual_review_steps", 0)
        if act_manual < exp_min_manual:
            errors.append(
                f"manual_review_steps {act_manual} < min_manual_review_steps {exp_min_manual}"
            )

    # min_rejected_steps
    exp_min_rejected = expected.get("min_rejected_steps")
    if exp_min_rejected is not None:
        act_rejected = actual.get("rejected_steps", 0)
        if act_rejected < exp_min_rejected:
            errors.append(
                f"rejected_steps {act_rejected} < min_rejected_steps {exp_min_rejected}"
            )

    # expected_final_status
    exp_final = expected.get("expected_final_status")
    if exp_final is not None:
        act_final = actual.get("final_status")
        if act_final != exp_final:
            errors.append(
                f"final_status: expected '{exp_final}', got '{act_final}'"
            )

    # required_artifacts (only checked when manifest is provided)
    exp_artifacts = expected.get("required_artifacts")
    if exp_artifacts is not None and manifest is not None:
        manifest_artifacts = manifest.get("artifacts", [])
        # The manifest does not self-reference, so treat "evidence_manifest" as
        # implicitly present when a manifest was successfully loaded.
        artifact_kinds = {a["kind"] for a in manifest_artifacts if a.get("exists")}
        artifact_kinds.add("evidence_manifest")
        for kind in exp_artifacts:
            if kind not in artifact_kinds:
                errors.append(
                    f"required artifact '{kind}' not found or does not exist in manifest"
                )

    # required_evidence_groups
    required_groups = expected.get("required_evidence_groups")
    if required_groups is not None:
        if not isinstance(required_groups, (list, tuple)):
            errors.append(
                f"required_evidence_groups must be a list, got {type(required_groups).__name__}"
            )
        elif manifest is None:
            errors.append(
                "required_evidence_groups requires manifest, but manifest is None"
            )
        elif not isinstance(manifest.get("evidence_groups"), dict):
            errors.append(
                "required_evidence_groups requires manifest.evidence_groups"
            )
        else:
            manifest_groups = manifest["evidence_groups"]
            for i, group_name in enumerate(required_groups):
                if not isinstance(group_name, str):
                    errors.append(
                        f"required_evidence_groups[{i}] must be a string, got {type(group_name).__name__}"
                    )
                    continue
                group = manifest_groups.get(group_name)
                if group is None or not group.get("available"):
                    errors.append(
                        f"required evidence group '{group_name}' is missing or unavailable"
                    )

    return (not errors, tuple(errors))
