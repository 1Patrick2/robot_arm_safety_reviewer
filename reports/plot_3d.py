"""Matplotlib 3D visualization for robot arm safety logs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from robot.safety.kinematics import forward_kinematics_6dof
from robot.safety.models import JointCommand, Scene
from robot.safety.trajectory import interpolate_joint_trajectory


def write_3d_plot(log_path: str | Path, output_dir: str | Path = "output_reports") -> Path:
    """Generate a PNG visualization from an execution log."""

    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("matplotlib is required to generate 3D visualizations") from exc

    payload = json.loads(Path(log_path).read_text(encoding="utf-8"))
    scene = Scene.from_dict(payload["scene"])
    command = JointCommand.from_dict(payload["command"])
    safety = payload["safety_result"]
    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )
    worst_step = safety.get("worst_step")
    worst_joints = trajectory[worst_step] if isinstance(worst_step, int) else None

    current_points = forward_kinematics_6dof(scene.robot, command.current_joints)
    target_points = forward_kinematics_6dof(scene.robot, command.target_joints)
    worst_points = forward_kinematics_6dof(scene.robot, worst_joints) if worst_joints else None

    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    current_label = "current = worst step" if worst_step == 0 else "current"
    _plot_arm(
        ax,
        current_points,
        label=current_label,
        color="tab:blue",
        alpha=0.85 if worst_step == 0 else 0.45,
        linestyle=":" if worst_step == 0 else "-",
        marker="x" if worst_step == 0 else "o",
        linewidth=2.2 if worst_step == 0 else 1.5,
    )
    _plot_arm(ax, target_points, label="target", color="tab:green", alpha=0.75)
    if worst_points:
        worst_label = f"worst step {worst_step}"
        _plot_arm(ax, worst_points, label=worst_label, color="tab:red", alpha=0.75 if worst_step == 0 else 0.95)
        _highlight_closest_link(ax, worst_points, safety)
    for obstacle in scene.obstacles:
        ax.scatter(
            [obstacle.position[0]],
            [obstacle.position[1]],
            [obstacle.position[2]],
            s=max(obstacle.radius * 2500, 60),
            color="orange",
            alpha=0.55,
            label=f"obstacle {obstacle.obstacle_id}",
        )

    ax.set_title(_plot_title(payload, safety))
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_zlabel("Z (m)")
    _set_equalish_axes(ax, [current_points, target_points] + ([worst_points] if worst_points else []), payload)
    ax.legend(loc="upper right")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    path = output / f"{payload['log_id']}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path


def _plot_arm(
    ax: Any,
    points,
    *,
    label: str,
    color: str,
    alpha: float,
    linestyle: str = "-",
    marker: str = "o",
    linewidth: float = 1.5,
) -> None:
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    zs = [point[2] for point in points]
    ax.plot(
        xs,
        ys,
        zs,
        marker=marker,
        linestyle=linestyle,
        linewidth=linewidth,
        color=color,
        alpha=alpha,
        label=label,
    )


def _highlight_closest_link(ax: Any, points, safety: dict[str, Any]) -> None:
    link_name = safety.get("closest_robot_link")
    link_index = _link_index(link_name)
    if link_index is None or link_index <= 0 or link_index >= len(points):
        return
    start = points[link_index - 1]
    end = points[link_index]
    ax.plot(
        [start[0], end[0]],
        [start[1], end[1]],
        [start[2], end[2]],
        color="red",
        linewidth=4,
        alpha=1.0,
        label=f"closest {link_name}",
    )
    mid = tuple((start[i] + end[i]) / 2 for i in range(3))
    ax.text(mid[0], mid[1], mid[2], f"{link_name}\nmin={safety['min_clearance']}m", color="red")


def _link_index(link_name: str | None) -> int | None:
    if not link_name or not link_name.startswith("link_"):
        return None
    try:
        return int(link_name.split("_", 1)[1])
    except ValueError:
        return None


def _plot_title(payload: dict[str, Any], safety: dict[str, Any]) -> str:
    closest = safety.get("closest_robot_link") or "no_link"
    obstacle = safety.get("closest_obstacle") or "no_obstacle"
    return (
        f"{payload['scene_id']} | {safety['decision']}/{safety['risk_level']} | "
        f"min_clearance={safety['min_clearance']}m | {closest}->{obstacle}"
    )


def _set_equalish_axes(ax: Any, point_groups, payload: dict[str, Any]) -> None:
    xs, ys, zs = [], [], []
    for points in point_groups:
        for point in points:
            xs.append(point[0])
            ys.append(point[1])
            zs.append(point[2])
    for obstacle in payload["scene"].get("obstacles", []):
        xs.append(obstacle["position"][0])
        ys.append(obstacle["position"][1])
        zs.append(obstacle["position"][2])

    margin = 0.15
    ax.set_xlim(min(xs) - margin, max(xs) + margin)
    ax.set_ylim(min(ys) - margin, max(ys) + margin)
    ax.set_zlim(max(0.0, min(zs) - margin), max(zs) + margin)
