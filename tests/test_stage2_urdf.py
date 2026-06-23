from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "bench/assets/robots/mock_realman_6dof"
URDF_PATH = ASSET_DIR / "robot.urdf"
README_PATH = ASSET_DIR / "README.md"

EXPECTED_LIMITS = {
    "joint1": (-3.14, 3.14),
    "joint2": (-1.57, 1.57),
    "joint3": (-2.2, 2.2),
    "joint4": (-3.14, 3.14),
    "joint5": (-1.8, 1.8),
    "joint6": (-3.14, 3.14),
}


def test_mock_realman_urdf_asset_exists_and_documents_boundary():
    assert URDF_PATH.exists()
    assert README_PATH.exists()
    readme = README_PATH.read_text(encoding="utf-8")
    assert "not a calibrated RealMan robot model" in readme


def test_mock_realman_urdf_defines_six_revolute_joints_with_limits():
    root = ET.parse(URDF_PATH).getroot()

    assert root.tag == "robot"
    assert root.attrib["name"] == "mock_realman_6dof"
    revolute_joints = [joint for joint in root.findall("joint") if joint.attrib.get("type") == "revolute"]

    assert [joint.attrib["name"] for joint in revolute_joints] == list(EXPECTED_LIMITS)
    for joint in revolute_joints:
        limit = joint.find("limit")
        assert limit is not None
        expected_lower, expected_upper = EXPECTED_LIMITS[joint.attrib["name"]]
        assert float(limit.attrib["lower"]) == expected_lower
        assert float(limit.attrib["upper"]) == expected_upper


def test_mock_realman_urdf_links_have_collision_geometry():
    root = ET.parse(URDF_PATH).getroot()
    links = {link.attrib["name"]: link for link in root.findall("link")}

    assert set(links) == {"base_link", "link_1", "link_2", "link_3", "link_4", "link_5", "link_6"}
    for link_name in ("link_1", "link_2", "link_3", "link_4", "link_5", "link_6"):
        collision = links[link_name].find("collision")
        assert collision is not None
        assert collision.find("geometry") is not None


def test_pybullet_can_load_mock_realman_urdf_when_installed():
    pybullet = pytest.importorskip("pybullet")

    client_id = pybullet.connect(pybullet.DIRECT)
    try:
        robot_id = pybullet.loadURDF(str(URDF_PATH), physicsClientId=client_id)
        joints = [
            pybullet.getJointInfo(robot_id, index, physicsClientId=client_id)
            for index in range(pybullet.getNumJoints(robot_id, physicsClientId=client_id))
        ]
        revolute_joints = [joint for joint in joints if joint[2] == pybullet.JOINT_REVOLUTE]

        assert len(revolute_joints) == 6
        assert [joint[1].decode("utf-8") for joint in revolute_joints] == list(EXPECTED_LIMITS)
    finally:
        pybullet.disconnect(client_id)
