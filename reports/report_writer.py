"""Markdown report writer for robot arm safety logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_markdown_report(log_payload: dict[str, Any], visualization_path: str | None = None) -> str:
    """Build a human-readable Markdown safety review report."""

    safety = log_payload["safety_result"]
    execution = log_payload["execution"]
    command = log_payload["command"]
    scene = log_payload["scene"]
    lines = [
        "# Robot Arm Safety Review Report",
        "",
        "## Task Summary",
        "",
        f"- Scene ID: `{log_payload['scene_id']}`",
        f"- Command ID: `{log_payload['command_id']}`",
        f"- Robot: `{log_payload['robot']}`",
        f"- Decision: `{safety['decision']}`",
        f"- Risk Level: `{safety['risk_level']}`",
        f"- Log ID: `{log_payload['log_id']}`",
        "",
        "## Robot Command",
        "",
        f"- Current joints: `{_format_vector(command['current_joints'])}`",
        f"- Target joints: `{_format_vector(command['target_joints'])}`",
        f"- Max joint delta: `{safety['max_joint_delta']}` rad",
        f"- Speed: `{command['speed']}`",
        f"- Source: `{command['source']}`",
        "",
        "## Safety Checks",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Joint limits | `{_pass_fail(safety['joint_limits_ok'])}` |",
        f"| Environment collision | `{_pass_fail(safety['trajectory_collision_free'])}` |",
        f"| Self collision | `{_self_collision_status(safety)}` |",
        f"| Minimum clearance | `{_clearance_status(scene, safety)}` |",
        f"| Closest link | `{safety.get('closest_robot_link')}` |",
        f"| Closest obstacle | `{safety.get('closest_obstacle')}` |",
        f"| Worst step | `{safety.get('worst_step')}` |",
        "",
        "## Scene Obstacles",
        "",
    ]
    obstacles = scene.get("obstacles", [])
    if obstacles:
        lines.extend([
            "| Obstacle | Type | Position | Radius |",
            "|---|---|---|---|",
        ])
        for obstacle in obstacles:
            lines.append(
                f"| `{obstacle['obstacle_id']}` | `{obstacle['type']}` | "
                f"`{_format_vector(obstacle['position'])}` | `{obstacle['radius']}` |"
            )
    else:
        lines.append("No obstacles are configured for this scene.")

    lines.extend([
        "",
        "## Critical Evidence",
        "",
    ])
    for item in safety.get("evidence", []):
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Violations",
        "",
    ])
    violations = safety.get("violations", [])
    if violations:
        lines.extend([
            "| Type | Link | Object | Step | Clearance | Message |",
            "|---|---|---|---|---|---|",
        ])
        for violation in violations:
            lines.append(
                f"| `{violation.get('type')}` | `{violation.get('link', '')}` | "
                f"`{violation.get('object', '')}` | `{violation.get('step', '')}` | "
                f"`{violation.get('clearance', '')}` | {violation.get('message', '')} |"
            )
    else:
        lines.append("No violations were recorded.")

    lines.extend([
        "",
        "## Gate Decision",
        "",
        f"- Mode: `{log_payload.get('mode', 'unknown')}`",
        f"- Backend: `{log_payload.get('environment', {}).get('backend', 'unknown')}`",
        f"- Simulated execution: `{execution['executed']}`",
        f"- Reason: `{execution['reason']}`",
        "",
        "## Recommended Action",
        "",
        *_recommended_action_lines(safety, execution),
    ])
    if visualization_path:
        lines.extend([
            "",
            "## Visualization",
            "",
            f"![3D safety visualization]({visualization_path})",
        ])

    return "\n".join(lines).rstrip() + "\n"


def write_markdown_report(
    log_path: str | Path,
    output_dir: str | Path = "output_reports",
    visualization_path: str | None = None,
) -> Path:
    """Write a Markdown report from an execution log."""

    payload = json.loads(Path(log_path).read_text(encoding="utf-8"))
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{payload['log_id']}.md"
    path.write_text(build_markdown_report(payload, visualization_path=visualization_path), encoding="utf-8")
    return path


def _format_vector(values: list[float]) -> str:
    return "[" + ", ".join(f"{float(item):.3f}" for item in values) + "]"


def _pass_fail(value: bool) -> str:
    return "PASS" if value else "FAIL"


def _self_collision_status(safety: dict[str, Any]) -> str:
    if not safety.get("self_collision_checked", False):
        return "NOT_CHECKED"
    return _pass_fail(bool(safety.get("self_collision_free")))


def _clearance_status(scene: dict[str, Any], safety: dict[str, Any]) -> str:
    if not scene.get("obstacles"):
        return "N/A - no obstacles"
    return f"{safety['min_clearance']} m"


def _recommended_action_lines(safety: dict[str, Any], execution: dict[str, Any]) -> list[str]:
    decision = safety["decision"]
    if decision == "approve" and execution["executed"]:
        return [
            "- Command passed the Stage 1 safety gate and simulated execution completed.",
            "- Keep the generated log for replay and audit.",
        ]
    if decision == "approve":
        return [
            "- Command passed the Stage 1 safety gate.",
            f"- Simulated execution did not complete because `{execution['reason']}`.",
        ]
    if decision == "manual_review":
        return [
            "- Do not execute automatically.",
            "- Request human review before sending this command to any robot adapter.",
        ]

    closest_obstacle = safety.get("closest_obstacle")
    closest_link = safety.get("closest_robot_link")
    if closest_obstacle and closest_link:
        reason = f"{closest_link} conflicts with {closest_obstacle}"
    else:
        reason = "the safety gate found a blocking violation"
    return [
        "- Do not execute this command.",
        f"- Reason: {reason}.",
        "- Suggested next step: change the target joints or request a collision-free trajectory.",
    ]
