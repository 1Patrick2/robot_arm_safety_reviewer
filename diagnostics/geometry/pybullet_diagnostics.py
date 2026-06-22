"""Structured PyBullet geometry diagnostics for benchmark tasks.
pybullet几何诊断，主要功能是重放基准测试任务的场景和轨迹，在PyBullet的DIRECT模式下捕获每个时间步的机器人链接位姿和与障碍物的最近点对信息，包括清晰度、接触点位置和法线等。这些诊断数据可以用来分析和比较不同后端的碰撞检查结果，以及理解模型决策背后的几何因素。"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from robot.safety.models import JointCommand, Scene
from robot.safety.trajectory import interpolate_joint_trajectory

from robot.backends.pybullet_backend import CONTACT_DISTANCE_INDEX, PyBulletBackend

POSITION_ON_ROBOT_INDEX = 5
POSITION_ON_OBSTACLE_INDEX = 6
NORMAL_ON_OBSTACLE_INDEX = 7

'''三件事，读scene,command，插值得到轨迹trajectory，然后调用diagnose_scene_geometry来重放场景并捕获诊断数据，最后返回一个结构化的字典结果。'''
def diagnose_task_geometry(task_dir: str | Path, *, backend: PyBulletBackend | None = None) -> dict[str, Any]:
    """Replay a benchmark task and return JSON-serializable PyBullet geometry diagnostics."""

    task_path = Path(task_dir)
    scene = Scene.from_json(task_path / "scene.json")
    command = JointCommand.from_json(task_path / "command.json")
    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )
    return diagnose_scene_geometry(
        scene=scene,
        command=command,
        trajectory=trajectory,
        task_id=task_path.name,
        backend=backend,
    )

'''这是核心函数，重放场景并捕获诊断数据。它会连接PyBullet的DIRECT模式，加载URDF模型，获取关节和链接信息，创建障碍物，遍历轨迹的每个时间步，更新机器人状态，执行碰撞检测，记录关节位姿和最近点的信息，最后返回一个包含所有诊断数据的字典。'''
def diagnose_scene_geometry(
    *,
    scene: Scene,
    command: JointCommand,
    trajectory: list[tuple[float, ...]],
    task_id: str | None = None,
    backend: PyBulletBackend | None = None,
) -> dict[str, Any]:
    """Replay a scene in PyBullet DIRECT mode and capture link poses plus closest-point pairs."""

    import pybullet

    backend = backend or PyBulletBackend()
    client_id = pybullet.connect(pybullet.DIRECT)
    try:
        robot_id = pybullet.loadURDF(
            str(backend.urdf_path),
            basePosition=scene.robot.base_position,
            baseOrientation=scene.robot.base_orientation,
            physicsClientId=client_id,
        )
        if robot_id < 0:
            raise RuntimeError(f"failed to load URDF: {backend.urdf_path}")

        revolute_joints = backend._revolute_joints(pybullet, client_id, robot_id)
        link_name_map = backend._link_name_map(pybullet, client_id, robot_id)
        obstacle_bodies = backend._create_sphere_obstacles(pybullet, client_id, scene.obstacles)
        steps = []
        worst_pair = None
        min_clearance = math.inf

        for step, joints in enumerate(trajectory):
            for joint_index, joint_value in zip(revolute_joints, joints):
                pybullet.resetJointState(robot_id, joint_index, joint_value, physicsClientId=client_id)
            pybullet.performCollisionDetection(physicsClientId=client_id)

            link_poses = _link_poses(pybullet, client_id, robot_id, link_name_map)
            closest_points = []
            for link_index, link_name in link_name_map.items():
                for obstacle, obstacle_body_id in obstacle_bodies:
                    points = pybullet.getClosestPoints(
                        bodyA=robot_id,
                        bodyB=obstacle_body_id,
                        distance=backend.closest_point_search_distance,
                        linkIndexA=link_index,
                        linkIndexB=-1,
                        physicsClientId=client_id,
                    )
                    for point in points:
                        observation = _closest_point_observation(
                            point=point,
                            step=step,
                            link_name=link_name,
                            obstacle_id=obstacle.obstacle_id,
                        )
                        closest_points.append(observation)
                        if observation["clearance"] < min_clearance:
                            min_clearance = observation["clearance"]
                            worst_pair = observation

            steps.append(
                {
                    "step": step,
                    "joints": [round(float(value), 6) for value in joints],
                    "link_poses": link_poses,
                    "closest_points": closest_points,
                }
            )

        return {
            "task_id": task_id or scene.scene_id,
            "scene_id": scene.scene_id,
            "command_id": command.command_id,
            "backend": backend.name,
            "mode": "DIRECT",
            "urdf_path": str(backend.urdf_path),
            "collision_method": backend.collision_method,
            "fidelity": "collision_geometry",
            "closest_point_search_distance": backend.closest_point_search_distance,
            "include_base_collision": backend.include_base_collision,
            "checked_links": list(link_name_map.values()),
            "obstacles": [
                {
                    "obstacle_id": obstacle.obstacle_id,
                    "position": [round(float(value), 6) for value in obstacle.position],
                    "radius": round(float(obstacle.radius), 6),
                }
                for obstacle in scene.obstacles
            ],
            "worst_pair": worst_pair or _empty_worst_pair(),
            "steps": steps,
        }
    finally:
        pybullet.disconnect(client_id)

'''这个函数用来获取机器人每个链接的位姿信息，返回一个字典，键是链接名称，值是另一个字典，包含position和orientation两个字段，都是经过_rounded_vector处理过的列表。'''
def _link_poses(pybullet, client_id: int, robot_id: int, link_name_map: dict[int, str]) -> dict[str, dict[str, Any]]:
    poses: dict[str, dict[str, Any]] = {}
    for link_index, link_name in link_name_map.items():
        if link_index == -1:
            position, orientation = pybullet.getBasePositionAndOrientation(robot_id, physicsClientId=client_id)
        else:
            link_state = pybullet.getLinkState(robot_id, link_index, physicsClientId=client_id)
            position, orientation = link_state[0], link_state[1]
        poses[link_name] = {
            "position": _rounded_vector(position),
            "orientation": _rounded_vector(orientation),
        }
    return poses


def _closest_point_observation(*, point, step: int, link_name: str, obstacle_id: str) -> dict[str, Any]:
    return {
        "step": step,
        "robot_link": link_name,
        "obstacle": obstacle_id,
        "clearance": round(float(point[CONTACT_DISTANCE_INDEX]), 6),
        "position_on_robot": _rounded_vector(point[POSITION_ON_ROBOT_INDEX]),
        "position_on_obstacle": _rounded_vector(point[POSITION_ON_OBSTACLE_INDEX]),
        "normal_on_obstacle": _rounded_vector(point[NORMAL_ON_OBSTACLE_INDEX]),
    }


def _empty_worst_pair() -> dict[str, Any]:
    return {
        "step": None,
        "robot_link": None,
        "obstacle": None,
        "clearance": 999.0,
        "position_on_robot": None,
        "position_on_obstacle": None,
        "normal_on_obstacle": None,
    }


def _rounded_vector(values) -> list[float]:
    return [round(float(value), 6) for value in values]
