from __future__ import annotations

from typing import Any


def collect_available_evidence_kinds(manifest: dict[str, Any]) -> set[str]:
    """Return the set of artifact kinds that exist on disk.

    ``evidence_manifest`` is always included because the manifest itself
    was successfully loaded to reach this function.
    """
    kinds = {"evidence_manifest"}
    artifacts = manifest.get("artifacts", [])
    if isinstance(artifacts, list):
        for a in artifacts:
            if isinstance(a, dict) and a.get("exists"):
                kinds.add(a.get("kind", ""))
    return {k for k in kinds if k}


def collect_available_evidence_groups(manifest: dict[str, Any]) -> set[str]:
    """Return the set of evidence group names that are available."""
    groups = manifest.get("evidence_groups", {})
    if not isinstance(groups, dict):
        return set()
    return {
        name
        for name, group in groups.items()
        if isinstance(group, dict) and group.get("available")
    }


def build_basic_evidence_refs(
    manifest: dict[str, Any],
    summary: dict[str, Any],
) -> tuple[str, ...]:
    """Build a tuple of basic evidence dot-paths from *summary* and *manifest*.

    Only includes summary fields that exist and are not ``None``.
    Always appends ``evidence_groups.geometry`` and ``evidence_groups.safety``
    when those groups are available.
    """
    refs: list[str] = []

    summary_fields = [
        "min_clearance",
        "closest_obstacle",
        "closest_robot_link",
        "worst_sequence_step_index",
    ]
    for f in summary_fields:
        if summary.get(f) is not None:
            refs.append(f"summary.{f}")

    available_groups = collect_available_evidence_groups(manifest)
    if "geometry" in available_groups:
        refs.append("evidence_groups.geometry")
    if "safety" in available_groups:
        refs.append("evidence_groups.safety")

    return tuple(refs)
