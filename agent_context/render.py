from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import AgentContext


def render_agent_context_json(context: AgentContext) -> dict[str, Any]:
    """Render the context as a JSON-serializable dict."""
    return context.to_dict()


def render_agent_context_markdown(context: AgentContext) -> str:
    """Render the context as a Markdown string."""
    lines = [
        "# Diagnostic Context",
        "",
        "## Episode Overview",
        f"- Episode ID: {context.episode_id}",
        f"- Sequence ID: {context.sequence_id or 'N/A'}",
        f"- Backend: {context.backend or 'N/A'}",
        f"- Device: {context.device or 'N/A'}",
        f"- Run Mode: {context.run_mode or 'N/A'}",
        "",
        "## Safety Summary",
        f"- Total Steps: {context.total_steps}",
        f"- Approved: {context.approved_steps}",
        f"- Executed: {context.executed_steps}",
        f"- Blocked: {context.blocked_steps}",
        f"- Rejected: {context.rejected_steps}",
        f"- Manual Review: {context.manual_review_steps}",
        f"- Min Clearance: {context.min_clearance!s}",
        f"- Worst Sequence Step: {context.worst_sequence_step_index!s}",
        f"- Backend Worst Step: {context.backend_worst_step!s}",
        f"- Closest Link: {context.closest_robot_link or 'N/A'}",
        f"- Closest Obstacle: {context.closest_obstacle or 'N/A'}",
        "",
        "## Critical Steps",
        "",
    ]

    if not context.critical_steps:
        lines.append("No critical steps selected.\n")
    else:
        lines.append("| Step | Decision | Risk | Executed | Blocked Reason | Min Clearance | Closest Link | Closest Obstacle |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for step in context.critical_steps:
            lines.append(
                f"| {step.step_index or '?'} "
                f"| {step.decision or '?'} "
                f"| {step.risk_level or '?'} "
                f"| {'yes' if step.executed else 'no'} "
                f"| {step.blocked_reason or '—'} "
                f"| {step.min_clearance!s} "
                f"| {step.closest_robot_link or '—'} "
                f"| {step.closest_obstacle or '—'} |"
            )
        lines.append("")

    lines += [
        "## Artifacts",
        "",
    ]
    if context.artifacts:
        for art in context.artifacts:
            lines.append(f"- **{art.kind}**: {art.path}")
        lines.append("")
    else:
        lines.append("No artifacts available.\n")

    lines += [
        "## Deterministic Safety Boundary",
        "",
        "This diagnostic context was built from structured episode metrics and deterministic rules.",
        "No LLM was involved in generating this context.",
        "",
        "## Known Limitations",
        "",
    ]
    for lim in context.limitations:
        lines.append(f"- {lim}")
    lines.append("")

    return "\n".join(lines)


def write_agent_context_files(
    context: AgentContext,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Write diagnostic_context.json and diagnostic_context.md.

    Returns (json_path, markdown_path).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # JSON
    json_path = output_dir / "diagnostic_context.json"
    json_path.write_text(
        json.dumps(render_agent_context_json(context), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Markdown
    md_path = output_dir / "diagnostic_context.md"
    md_path.write_text(render_agent_context_markdown(context), encoding="utf-8")

    return json_path, md_path
