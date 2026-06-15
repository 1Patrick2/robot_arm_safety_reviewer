from __future__ import annotations

from pathlib import Path

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


def write_trajectory_overview(episode_dir: Path, output_dir: Path | None = None) -> Path:
    """Plot end-effector target positions per step and save as *trajectory_overview.png*."""
    plt = _get_plt()
    bundle = load_episode(episode_dir)
    target_dir = output_dir or episode_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    robot = _default_robot()
    steps = bundle.steps

    approved_pts: list[tuple[int, float, float, float]] = []
    blocked_pts: list[tuple[int, float, float, float]] = []

    for idx, step in enumerate(steps):
        obs = step.get("observation", {})
        action = step.get("proposed_action", {})
        jp = obs.get("joint_positions")
        tj = action.get("target_joints")
        if not jp or not tj:
            continue

        target_fk = forward_kinematics_6dof(robot, tj)
        ee = target_fk[-1]
        decision = step.get("safety_result", {}).get("decision")
        if decision == "approve":
            approved_pts.append((idx + 1, ee[0], ee[1], ee[2]))
        else:
            blocked_pts.append((idx + 1, ee[0], ee[1], ee[2]))

    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    ax.set_title("Episode Trajectory Overview (End-Effector Targets)")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")

    if approved_pts:
        ax.scatter(
            [p[1] for p in approved_pts], [p[2] for p in approved_pts], [p[3] for p in approved_pts],
            marker="o", color="green", s=60, label="approved",
        )
        for p in approved_pts:
            ax.text(p[1], p[2], p[3], f"  {p[0]}", fontsize=8)

    if blocked_pts:
        ax.scatter(
            [p[1] for p in blocked_pts], [p[2] for p in blocked_pts], [p[3] for p in blocked_pts],
            marker="x", color="red", s=80, label="blocked",
        )
        for p in blocked_pts:
            ax.text(p[1], p[2], p[3], f"  {p[0]}", fontsize=8)

    ax.legend()
    plot_path = target_dir / "trajectory_overview.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return plot_path
