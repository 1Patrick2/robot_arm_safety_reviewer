"""URDF-vs-mock geometry calibration diagnostics.
URDF与mock的校准诊断，主要功能是比较PyBullet URDF碰撞轴与我们之前实现的mock FK段之间的几何关系。它会重放基准测试任务的场景和轨迹，在PyBullet中捕获每个时间步的机器人链接位姿和与障碍物的最近点对信息，然后把这些信息与mock的FK段进行对比分析，计算长度差异、端点对齐误差等指标，最后给出一个结论分类和推荐
"""

from __future__ import annotations

'''这个文件比pybullet_diagnostics更进一步，后者是回答pybullet自己看到的worst_pair是什么，而这个文件是回答pybullet的worst_pair和mock fk segment为什么不一致，是urdf模型的问题还是mock kinematic模型的问题。这个诊断对于理解和调试pybullet后端的几何实现非常有帮助，可以指导我们是否需要调整urdf模型或者接受一定的误差范围。'''

import math
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from robot.safety.collision import distance_segment_to_point, segment_sphere_clearance
from robot.safety.kinematics import forward_kinematics_6dof
from robot.safety.models import JointCommand, Scene
from robot.safety.trajectory import interpolate_joint_trajectory

from robot.backends.pybullet_backend import PyBulletBackend
from diagnostics.geometry.pybullet_diagnostics import diagnose_task_geometry


'''解析urdf里的box collision geometry，提取每个链接的碰撞盒信息，包括原点位置、尺寸等，返回一个字典，键是链接名称，值是另一个字典'''
def parse_urdf_collision_boxes(urdf_path: str | Path) -> dict[str, dict[str, Any]]:
    """Extract simple box collision geometry from the mock URDF."""

    root = ET.parse(urdf_path).getroot()
    boxes: dict[str, dict[str, Any]] = {}
    for link in root.findall("link"):
        link_name = str(link.attrib["name"])
        collision = link.find("collision")
        if collision is None:
            continue
        geometry = collision.find("geometry")
        box = geometry.find("box") if geometry is not None else None
        if box is None:
            continue
        origin = collision.find("origin")
        boxes[link_name] = {
            "origin_xyz": _float_list(origin.attrib.get("xyz", "0 0 0") if origin is not None else "0 0 0"),
            "origin_rpy": _float_list(origin.attrib.get("rpy", "0 0 0") if origin is not None else "0 0 0"),
            "size": _float_list(box.attrib["size"]),
        }
    return boxes


'''核心函数，读取scene/command，插值得到轨迹trajectory，然后调用diagnose_scene_geometry来重放场景并捕获诊断数据pybullet diagnostics,取pybullet worst step的joints，计算mock在同一joints下的closest segment，最后返回一个结构化的字典结果，包括pybullet和mock的worst step信息，以及对比分析的结论和推荐。'''
def calibrate_task_geometry(task_dir: str | Path, *, backend: PyBulletBackend | None = None) -> dict[str, Any]:
    """Compare mock FK segments with PyBullet URDF collision-axis geometry for one task."""

    task_path = Path(task_dir)
    backend = backend or PyBulletBackend()
    scene = Scene.from_json(task_path / "scene.json")
    command = JointCommand.from_json(task_path / "command.json")
    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )
    diagnostic = diagnose_task_geometry(task_path, backend=backend)
    worst_step = diagnostic["worst_pair"]["step"]
    if worst_step is None:
        worst_step = 0

    joints = trajectory[worst_step]
    mock_points = forward_kinematics_6dof(scene.robot, joints)

    '''解析urdf collision boxes'''
    boxes = parse_urdf_collision_boxes(backend.urdf_path)
    obstacle_id = diagnostic["worst_pair"]["obstacle"]
    obstacle = next((item for item in scene.obstacles if item.obstacle_id == obstacle_id), None)

    '''这是mock与pybullet worst step的对比，计算mock在pybullet worst step的joints下的closest segment信息。'''
    mock_at_pybullet_worst_step = _mock_closest_segment(mock_points, scene, obstacle, step=worst_step)

    ''''这是mock轨迹上的overall worst，计算mock在整个轨迹上的closest segment信息，看看是否有比pybullet worst step更糟糕的情况，如果有，说明可能是pybullet的worst step没有完全捕捉到mock的worst case。'''
    mock_overall_worst = _mock_trajectory_worst(trajectory, scene, obstacle)


    link_calibration = _link_calibration(
        boxes=boxes,
        diagnostic_step=diagnostic["steps"][worst_step],
        mock_points=mock_points,
        robot_link_lengths=scene.robot.link_lengths,
    )
    conclusion = _conclusion(
        pybullet_link=diagnostic["worst_pair"]["robot_link"],
        mock_link=mock_overall_worst["closest_link"],
        link_calibration=link_calibration,
    )

    return {
        "task_id": task_path.name,
        "scene_id": scene.scene_id,
        "command_id": command.command_id,
        "worst_step": worst_step,
        "joints": [round(float(value), 6) for value in joints],
        "pybullet": {
            "closest_link": diagnostic["worst_pair"]["robot_link"],
            "closest_obstacle": diagnostic["worst_pair"]["obstacle"],
            "clearance": diagnostic["worst_pair"]["clearance"],
            "position_on_robot": diagnostic["worst_pair"]["position_on_robot"],
            "position_on_obstacle": diagnostic["worst_pair"]["position_on_obstacle"],
            "collision_method": diagnostic["collision_method"],
        },
        "mock_at_pybullet_worst_step": mock_at_pybullet_worst_step,
        "mock_overall_worst": mock_overall_worst,
        "link_calibration": link_calibration,
        "conclusion": conclusion,
        "recommendation": _recommendation(conclusion["category"]),
    }


def _mock_trajectory_worst(trajectory, scene: Scene, obstacle) -> dict[str, Any]:
    if obstacle is None:
        return _empty_mock_result(step=None)

    best: dict[str, Any] | None = None
    for step, joints in enumerate(trajectory):
        points = forward_kinematics_6dof(scene.robot, joints)
        candidate = _mock_closest_segment(points, scene, obstacle, step=step)
        if best is None or candidate["clearance"] < best["clearance"]:
            best = candidate
    return best or _empty_mock_result(step=None)


def _mock_closest_segment(mock_points, scene: Scene, obstacle, *, step: int | None = None) -> dict[str, Any]:
    if obstacle is None:
        return _empty_mock_result(step=step)

    best: dict[str, Any] | None = None
    for link_index, (start, end) in enumerate(zip(mock_points, mock_points[1:]), start=1):
        clearance = segment_sphere_clearance(start, end, obstacle, scene.robot.link_radius)
        candidate = {
            "step": step,
            "closest_link": f"link_{link_index}",
            "closest_obstacle": obstacle.obstacle_id,
            "clearance": round(clearance, 6),
            "segment_start": _rounded_vector(start),
            "segment_end": _rounded_vector(end),
            "segment_to_obstacle_center_distance": round(distance_segment_to_point(start, end, obstacle.position), 6),
        }
        if best is None or candidate["clearance"] < best["clearance"]:
            best = candidate
    return best or _empty_mock_result(step=step)


def _empty_mock_result(*, step: int | None) -> dict[str, Any]:
    return {
        "step": step,
        "closest_link": None,
        "closest_obstacle": None,
        "clearance": 999.0,
        "segment_start": None,
        "segment_end": None,
        "segment_to_obstacle_center_distance": None,
    }


'''这是把URDF collision box的主轴端点变换到world坐标，然后和mock FK的segment 的首尾端点做比较，计算长度差异和端点对齐误差。可以判断URDF link 长度是不是和 mock link 长度一样？如果长度一样，那是不是 pose / axis / kinematics 不一样？'''
def _link_calibration(
    *,
    boxes: dict[str, dict[str, Any]],
    diagnostic_step: dict[str, Any],
    mock_points,
    robot_link_lengths,
) -> dict[str, dict[str, Any]]:
    calibration: dict[str, dict[str, Any]] = {}
    for link_index in range(1, 7):
        link_name = f"link_{link_index}"
        box = boxes[link_name]
        pose = diagnostic_step["link_poses"][link_name]
        py_start, py_end, axis = _collision_axis_world_endpoints(box, pose)
        mock_start = mock_points[link_index - 1]
        mock_end = mock_points[link_index]
        direct_error = _distance(mock_start, py_start) + _distance(mock_end, py_end)
        swapped_error = _distance(mock_start, py_end) + _distance(mock_end, py_start)
        endpoint_alignment_error = min(direct_error, swapped_error) / 2.0
        urdf_length = max(box["size"])
        mock_length = float(robot_link_lengths[link_index - 1])
        calibration[link_name] = {
            "mock_segment_start": _rounded_vector(mock_start),
            "mock_segment_end": _rounded_vector(mock_end),
            "pybullet_collision_axis_start": py_start,
            "pybullet_collision_axis_end": py_end,
            "urdf_collision_origin_xyz": box["origin_xyz"],
            "urdf_collision_size": box["size"],
            "urdf_axis": axis,
            "urdf_length": round(urdf_length, 6),
            "mock_length": round(mock_length, 6),
            "length_delta": round(urdf_length - mock_length, 6),
            "endpoint_alignment_error": round(endpoint_alignment_error, 6),
        }
    return calibration


def _collision_axis_world_endpoints(box: dict[str, Any], pose: dict[str, Any]) -> tuple[list[float], list[float], str]:
    size = box["size"]
    axis_index = max(range(3), key=lambda index: size[index])
    half_length = size[axis_index] / 2.0
    axis = ["x", "y", "z"][axis_index]
    local_start = list(box["origin_xyz"])
    local_end = list(box["origin_xyz"])
    local_start[axis_index] -= half_length
    local_end[axis_index] += half_length
    world_start = _transform_local_point(local_start, pose["position"], pose["orientation"])
    world_end = _transform_local_point(local_end, pose["position"], pose["orientation"])
    return world_start, world_end, axis


def _transform_local_point(local_point, world_position, quaternion) -> list[float]:
    rotated = _rotate_vector_by_quaternion(local_point, quaternion)
    return _rounded_vector([rotated[index] + world_position[index] for index in range(3)])


def _rotate_vector_by_quaternion(vector, quaternion) -> list[float]:
    x, y, z, w = (float(value) for value in quaternion)
    vx, vy, vz = (float(value) for value in vector)
    # q * v * q^-1, expanded to avoid adding a dependency just for diagnostics.
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return [
        vx + w * tx + (y * tz - z * ty),
        vy + w * ty + (z * tx - x * tz),
        vz + w * tz + (x * ty - y * tx),
    ]


'''自动归因，通过max_length_delta,max_alignment_error以及pybullet_link和mock_link的对比，来判断是不是URDF尺寸不一致，如果尺寸没问题再判断是不是运动学/姿态不一致'''
def _conclusion(*, pybullet_link: str | None, mock_link: str | None, link_calibration: dict[str, Any]) -> dict[str, str]:
    max_length_delta = max(abs(item["length_delta"]) for item in link_calibration.values())
    max_alignment_error = max(item["endpoint_alignment_error"] for item in link_calibration.values())
    if max_length_delta > 0.02:
        category = "geometry_size_mismatch"
        summary = "URDF collision lengths differ materially from mock link lengths."
    elif pybullet_link != mock_link or max_alignment_error > 0.05:
        category = "kinematic_model_mismatch"
        summary = (
            "URDF collision lengths match the mock lengths, but link poses/attribution differ; "
            "this points to mock-vs-URDF kinematic model differences."
        )
    else:
        category = "calibrated"
        summary = "URDF collision axes are aligned with the mock FK segments within the current tolerance."
    return {"category": category, "summary": summary}

'''根据结论给建议'''
def _recommendation(category: str) -> str:
    if category == "geometry_size_mismatch":
        return "Inspect and adjust URDF collision sizes/origins before adding GUI replay."
    if category == "kinematic_model_mismatch":
        return (
            "Do not force PyBullet to match the mock backend exactly. Treat mock as a deterministic baseline "
            "and consider backend-specific benchmark expectations."
        )
    return "Proceed to visual diagnostics or GUI replay if a human-readable demo is needed."


def _float_list(raw: str) -> list[float]:
    return [float(item) for item in raw.split()]


def _distance(first, second) -> float:
    return math.sqrt(sum((float(a) - float(b)) ** 2 for a, b in zip(first, second)))


def _rounded_vector(values) -> list[float]:
    return [round(float(value), 6) for value in values]
