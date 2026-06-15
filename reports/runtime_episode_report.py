from __future__ import annotations

from pathlib import Path

from robot_runtime.episode_loader import RuntimeEpisodeBundle, load_episode


def build_runtime_episode_markdown(bundle: RuntimeEpisodeBundle) -> str:
    """Build a Markdown summary string from an episode bundle."""
    meta = bundle.metadata
    steps = bundle.steps

    total = len(steps)
    approved = sum(1 for s in steps if s.get("safety_result", {}).get("decision") == "approve")
    executed = sum(1 for s in steps if s.get("executed"))
    blocked = sum(1 for s in steps if s.get("blocked_reason") is not None)
    rejected = sum(1 for s in steps if s.get("safety_result", {}).get("decision") == "reject")
    manual_review = sum(1 for s in steps if s.get("safety_result", {}).get("decision") == "manual_review")

    lines = [
        "# Runtime Episode Summary",
        "",
        "## Overview",
        f"- Episode ID: {meta.get('episode_id', 'unknown')}",
        f"- Backend: {meta.get('backend', 'unknown')}",
        f"- Robot: {meta.get('robot', 'unknown')}",
        f"- Action Source: {meta.get('action_source', 'unknown')}",
        f"- Scene Provider: {meta.get('scene_provider', 'unknown')}",
        f"- Total Steps: {total}",
        f"- Approved: {approved}",
        f"- Executed: {executed}",
        f"- Blocked: {blocked}",
        f"- Rejected: {rejected}",
        f"- Manual Review: {manual_review}",
        "",
        "## Step Table",
        "",
        "| Step | Decision | Risk | Executed | Blocked Reason | Min Clearance | Closest Link | Closest Obstacle |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for step in steps:
        sr = step.get("safety_result", {})
        step_id = step.get("step_id", "?")
        decision = sr.get("decision", "?")
        risk = sr.get("risk_level", "?")
        exe = "yes" if step.get("executed") else "no"
        reason = step.get("blocked_reason") or "—"
        clearance = sr.get("min_clearance", "?")
        link = sr.get("closest_robot_link") or "—"
        obstacle = sr.get("closest_obstacle") or "—"
        lines.append(f"| {step_id} | {decision} | {risk} | {exe} | {reason} | {clearance} | {link} | {obstacle} |")

    lines += [
        "",
        "## Artifacts",
        "- `steps.jsonl`",
        "- `metadata.json`",
        "",
    ]

    return "\n".join(lines)


def write_runtime_episode_report(
    episode_dir: Path,
    output_dir: Path | None = None,
) -> Path:
    """Load an episode and write a Markdown summary report."""
    bundle = load_episode(episode_dir)
    md = build_runtime_episode_markdown(bundle)
    target_dir = output_dir or episode_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    report_path = target_dir / "episode_summary.md"
    report_path.write_text(md, encoding="utf-8")
    return report_path
