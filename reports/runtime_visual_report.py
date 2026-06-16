from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robot_runtime.episode_loader import load_episode
from robot_safety.kinematics import forward_kinematics_6dof
from robot_safety.models import RobotModel

# Default mock robot parameters used when the originating scene is unavailable.
_DEFAULT_LINK_LENGTHS = (0.18, 0.32, 0.28, 0.2, 0.14, 0.1)
_DEFAULT_LINK_RADIUS = 0.03


def _get_plt():
    try:
        import matplotlib  # noqa: PLC0415
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # noqa: PLC0415
        return plt
    except ImportError:
        raise RuntimeError(
            "matplotlib is required to generate visual artifacts; "
            "install it with: pip install matplotlib"
        ) from None


def _default_robot() -> RobotModel:
    import robot_safety.models as m  # noqa: PLC0415
    return RobotModel(
        robot_id="mock",
        model_type="mock_6dof",
        model_version="1.0",
        joint_names=("j1", "j2", "j3", "j4", "j5", "j6"),
        joint_limits=(
            m.JointLimit(-3.14, 3.14),
            m.JointLimit(-3.14, 3.14),
            m.JointLimit(-3.14, 3.14),
            m.JointLimit(-3.14, 3.14),
            m.JointLimit(-3.14, 3.14),
            m.JointLimit(-3.14, 3.14),
        ),
        link_lengths=_DEFAULT_LINK_LENGTHS,
        link_radius=_DEFAULT_LINK_RADIUS,
    )


def write_clearance_curve(episode_dir: Path, output_dir: Path | None = None) -> Path:
    """Plot action-level min_clearance per step and save as *clearance_curve.png*."""
    plt = _get_plt()
    bundle = load_episode(episode_dir)
    target_dir = output_dir or episode_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    steps = bundle.steps
    step_indices = list(range(1, len(steps) + 1))
    clearances = []
    for s in steps:
        sr = s.get("safety_result", {})
        c = sr.get("min_clearance")
        clearances.append(c)

    fig, ax = plt.subplots()

    # Sentinel 999.0 from the mock backend means "no obstacle nearby".
    # When all values are the sentinel, label the chart clearly.
    if clearances and all(c is not None and c >= 999.0 for c in clearances):
        ax.text(0.5, 0.5, "No obstacles in scene — clearance check skipped",
                transform=ax.transAxes, ha="center", va="center", fontsize=12,
                style="italic", color="gray")
        ax.set_xlabel("Sequence Step Index")
        ax.set_ylabel("Min Clearance (m)")
        ax.set_title("Action-Level Clearance Curve (no obstacles)")
    else:
        ax.plot(step_indices, clearances, marker="o", linestyle="-", label="min_clearance")
        ax.axhline(y=0, color="red", linestyle="--", linewidth=0.8, label="zero clearance")
        ax.set_xlabel("Sequence Step Index")
        ax.set_ylabel("Min Clearance (m)")
        ax.set_title("Action-Level Clearance Curve")
        ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)

    plot_path = target_dir / "clearance_curve.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return plot_path


def write_trajectory_evidence_data(
    episode_dir: Path,
    steps: list[dict[str, Any]],
    *,
    robot_model_source: str = "default_mock_fallback",
    scene_path: Path | None = None,
) -> Path:
    """Write trajectory_overview_data.json alongside the PNG.

    This structured data enables deterministic testing of FK correctness
    without relying on pixel-level image comparison.
    """
    ep_dir = Path(episode_dir)
    robot = _default_robot()
    meta_path = ep_dir / "metadata.json"
    meta = {}
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))

    step_records: list[dict[str, Any]] = []
    for idx, step in enumerate(steps):
        action = step.get("proposed_action", {})
        tj = action.get("target_joints")
        if not tj:
            continue
        fk = forward_kinematics_6dof(robot, tj)
        step_records.append({
            "step_index": step.get("step_index") or (idx + 1),
            "decision": step.get("safety_result", {}).get("decision"),
            "target_joints": list(tj),
            "fk_points": [list(p) for p in fk],
            "end_effector": list(fk[-1]),
        })

    payload: dict[str, Any] = {
        "episode_id": meta.get("episode_id", ep_dir.name),
        "scene_path": meta.get("scene_path"),
        "robot_model_source": robot_model_source,
        "joint_names": ["j1", "j2", "j3", "j4", "j5", "j6"],
        "joint_units": "rad",
        "steps": step_records,
    }

    data_path = ep_dir / "trajectory_overview_data.json"
    data_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return data_path


def write_trajectory_overview(episode_dir: Path, output_dir: Path | None = None) -> Path:
    """Plot the robot arm FK chain for each step's target configuration.

    Shows:
    - Full arm link chain (base → joint1 → ... → end-effector) for each step.
    - Green arms for approved steps, red arms for blocked/rejected steps.
    - Trajectory path connecting end-effector positions in sequence order.
    - Step index labels at each end-effector position.
    """
    plt = _get_plt()
    bundle = load_episode(episode_dir)
    target_dir = output_dir or episode_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    robot = _default_robot()
    steps = bundle.steps

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection="3d")
    ax.set_title("Episode Trajectory Overview (Robot Arm Configurations)")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")

    all_ee: list[tuple[int, float, float, float, str]] = []  # (idx, x, y, z, decision)

    for idx, step in enumerate(steps):
        action = step.get("proposed_action", {})
        tj = action.get("target_joints")
        if not tj:
            continue

        target_fk = forward_kinematics_6dof(robot, tj)
        decision = step.get("safety_result", {}).get("decision", "unknown")
        is_approved = decision == "approve"
        color = "green" if is_approved else "red"
        alpha = 0.7 if is_approved else 0.9
        ls = "-" if is_approved else "--"

        # Draw full arm FK chain
        fk_x = [p[0] for p in target_fk]
        fk_y = [p[1] for p in target_fk]
        fk_z = [p[2] for p in target_fk]
        ax.plot(fk_x, fk_y, fk_z, color=color, alpha=alpha, linestyle=ls,
                linewidth=2, marker="o", markersize=4, label=f"step {idx+1}" if idx == 0 else "")

        # Mark end-effector
        ee = target_fk[-1]
        marker = "o" if is_approved else "x"
        ax.scatter([ee[0]], [ee[1]], [ee[2]], marker=marker,
                   color=color, s=100 if is_approved else 120, zorder=5)
        ax.text(ee[0], ee[1], ee[2], f"  {idx + 1}", fontsize=9, color=color)

        all_ee.append((idx + 1, ee[0], ee[1], ee[2], decision))

    # Connect end-effector trajectory path in sequence order
    if len(all_ee) > 1:
        ee_seq_x = [p[1] for p in all_ee]
        ee_seq_y = [p[2] for p in all_ee]
        ee_seq_z = [p[3] for p in all_ee]
        ax.plot(ee_seq_x, ee_seq_y, ee_seq_z, color="gray", alpha=0.4,
                linestyle=":", linewidth=1, label="trajectory path")

    ax.legend(loc="upper left", fontsize=8)
    # Auto-scale axes to fit all FK points with a margin
    all_x = []
    all_y = []
    all_z = []
    for step in steps:
        action = step.get("proposed_action", {})
        tj = action.get("target_joints")
        if tj:
            fk = forward_kinematics_6dof(robot, tj)
            all_x.extend(p[0] for p in fk)
            all_y.extend(p[1] for p in fk)
            all_z.extend(p[2] for p in fk)
    if all_x:
        margin = 0.1
        ax.set_xlim(min(all_x) - margin, max(all_x) + margin)
        ax.set_ylim(min(all_y) - margin, max(all_y) + margin)
        ax.set_zlim(min(all_z) - margin, max(all_z) + margin)

    plot_path = target_dir / "trajectory_overview.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Write structured evidence data alongside the PNG
    write_trajectory_evidence_data(episode_dir, steps)

    return plot_path
