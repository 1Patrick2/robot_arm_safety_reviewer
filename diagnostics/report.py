from __future__ import annotations

from typing import Any

from .tools import get_episode_summary, get_worst_step, list_critical_steps, get_artifact_index


def build_diagnostic_report(bundle: dict[str, Any]) -> str:
    """Generate a deterministic diagnostic report from a context bundle.

    The report is entirely deterministic — no LLM involved.
    """
    summary = get_episode_summary(bundle)
    worst = get_worst_step(bundle)
    steps = list_critical_steps(bundle)
    artifacts = get_artifact_index(bundle)
    limitations = bundle.get("limitations", [])

    lines = [
        "# Diagnostic Report",
        "",
        "## Episode Overview",
        f"- Episode ID: {summary.get('episode_id', '?')}",
        f"- Sequence ID: {summary.get('sequence_id', 'N/A')}",
        f"- Backend: {summary.get('backend', 'N/A')}",
        "",
        "## Safety Summary",
        f"- Total Steps: {summary.get('total_steps', 0)}",
        f"- Approved: {summary.get('approved', 0)}",
        f"- Executed: {summary.get('executed', 0)}",
        f"- Blocked: {summary.get('blocked', 0)}",
        f"- Rejected: {summary.get('rejected', 0)}",
        f"- Manual Review: {summary.get('manual_review', 0)}",
        f"- Min Clearance: {summary.get('min_clearance', 'N/A')}",
        "",
    ]

    if worst:
        lines += [
            "## Worst Step Analysis",
            f"- Step Index: {worst.get('step_index', '?')}",
            f"- Decision: {worst.get('decision', '?')}",
            f"- Risk Level: {worst.get('risk_level', '?')}",
            f"- Min Clearance: {worst.get('min_clearance', '?')}",
            f"- Closest Link: {worst.get('closest_robot_link', 'N/A')}",
            f"- Closest Obstacle: {worst.get('closest_obstacle', 'N/A')}",
            "",
        ]

    if steps:
        lines += [
            "## Critical Step Table",
            "",
            "| Step | Decision | Risk | Min Clearance | Closest Link | Closest Obstacle |",
            "|---|---|---|---|---|---|",
        ]
        for s in steps:
            lines.append(
                f"| {s.get('step_index', '?')} "
                f"| {s.get('decision', '?')} "
                f"| {s.get('risk_level', '?')} "
                f"| {s.get('min_clearance', '?')} "
                f"| {s.get('closest_robot_link', 'N/A')} "
                f"| {s.get('closest_obstacle', 'N/A')} |"
            )
        lines.append("")

    if artifacts:
        lines += [
            "## Artifact References",
            "",
        ]
        for a in artifacts:
            desc = a.get("description") or a.get("kind", "?")
            lines.append(f"- **{desc}**: `{a.get('path', '?')}`")
        lines.append("")

    lines += [
        "## Human Review Focus",
        "",
    ]
    if worst:
        lines.append(
            f"The most critical step (step {worst.get('step_index', '?')}) "
            f"has a decision of **{worst.get('decision', '?')}** "
            f"with clearance **{worst.get('min_clearance', '?')}**."
        )
        lines.append(
            f"The closest obstacle is **{worst.get('closest_obstacle', 'unknown')}** "
            f"at link **{worst.get('closest_robot_link', 'unknown')}**."
        )
        lines.append("")
    else:
        lines.append("No critical steps identified.\n")

    lines += [
        "## Deterministic Safety Boundary",
        "",
    ]
    for lim in limitations:
        lines.append(f"- {lim}")
    lines.append("")

    return "\n".join(lines)
