"""Capability test: robot safety pipeline — scene, sequence, sandbox, runtime,
collision geometry, kinematics, decision logic."""

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "bench" / "samples" / "policy_sequences"
BENCH = ROOT / "bench" / "sim_robot_arm"


# ── Sandbox pipeline ──────────────────────────────────────────────────────

def test_sandbox_produces_approve_for_safe_sequence(tmp_path):
    from application.sandbox_service import SandboxRunRequest, run_sandbox
    result = run_sandbox(SandboxRunRequest(
        sequence_path=SAMPLES / "simple_safe_sequence.json",
        scene_path=BENCH / "simple_joint_move_001" / "scene.json",
        backend_name="mock",
        output_root=tmp_path / "sandbox",
    ))
    r = result.sequence_runtime_result
    assert r.total_steps == 2
    assert r.approved_steps == 2
    assert r.executed_steps == 2
    ep_dir = r.episode_dir
    assert (ep_dir / "metadata.json").exists()
    assert (ep_dir / "steps.jsonl").exists()


def test_sandbox_produces_reject_for_collision_sequence(tmp_path):
    from application.sandbox_service import SandboxRunRequest, run_sandbox
    result = run_sandbox(SandboxRunRequest(
        sequence_path=SAMPLES / "collision_sequence.json",
        scene_path=BENCH / "obstacle_collision_001" / "scene.json",
        backend_name="mock",
        output_root=tmp_path / "sandbox",
    ))
    r = result.sequence_runtime_result
    assert r.rejected_steps >= 1
    assert r.blocked_steps >= 1


def test_backend_factory_creates_mock():
    from robot.backends.backend_factory import create_backend
    backend = create_backend("mock")
    assert backend.name == "mock"


def test_run_sandbox_creates_visual_artifacts(tmp_path):
    from application.sandbox_service import SandboxRunRequest, run_sandbox
    result = run_sandbox(SandboxRunRequest(
        sequence_path=SAMPLES / "simple_safe_sequence.json",
        scene_path=BENCH / "simple_joint_move_001" / "scene.json",
        backend_name="mock",
        output_root=tmp_path / "sandbox",
    ))
    ep_dir = result.sequence_runtime_result.episode_dir
    assert (ep_dir / "episode_summary.md").exists()
    assert (ep_dir / "clearance_curve.png").exists()
    assert (ep_dir / "trajectory_overview.png").exists()


# ── Collision geometry ────────────────────────────────────────────────────

def test_distance_segment_to_point_returns_perpendicular_distance():
    """Stage1 migration: segment-to-point distance contract."""
    from robot.safety.models import Point3D
    from robot.safety.collision import distance_segment_to_point
    p1 = Point3D((0.0, 0.0, 0.0))
    p2 = Point3D((1.0, 0.0, 0.0))
    point = Point3D((0.5, 0.2, 0.0))
    dist = distance_segment_to_point(p1, p2, point)
    assert dist == pytest.approx(0.2, abs=1e-10)


def test_segment_sphere_clearance_is_signed():
    """Stage1 migration: signed clearance (negative = collision)."""
    from robot.safety.models import Point3D, SphereObstacle
    from robot.safety.collision import segment_sphere_clearance
    p1 = Point3D((0.0, 0.0, 0.0))
    p2 = Point3D((1.0, 0.0, 0.0))
    sphere = SphereObstacle(obstacle_id="s1", position=Point3D((0.5, 0.1, 0.0)), radius=0.08)
    clearance = segment_sphere_clearance(p1, p2, sphere, link_radius=0.025)
    assert clearance < 0.0  # sphere overlaps the link


def test_check_trajectory_collision_reports_closest_link_and_obstacle():
    """Stage1 migration: collision result fields contract."""
    from robot.safety.models import Scene
    from robot.safety.collision import check_trajectory_collision
    scene = Scene.from_json(str(BENCH / "obstacle_collision_001" / "scene.json"))
    trajectory = [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), (0.5, 0.0, 0.0, 0.0, 0.0, 0.0)]
    result = check_trajectory_collision(trajectory=trajectory, robot=scene.robot, obstacles=scene.obstacles)
    assert result.collision_free is False
    assert result.min_clearance < 0.0
    assert result.closest_robot_link is not None
    assert result.closest_obstacle is not None
    assert result.worst_step is not None


# ── Forward kinematics ────────────────────────────────────────────────────

def test_forward_kinematics_outputs_seven_points_for_six_dof():
    """Stage1 migration: FK produces base + 6 link positions."""
    from robot.safety.kinematics import forward_kinematics_6dof
    from robot.safety.models import Scene
    scene = Scene.from_json(str(BENCH / "simple_joint_move_001" / "scene.json"))
    fk = forward_kinematics_6dof(robot=scene.robot, joints=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    assert len(fk) == 7
    assert fk[0] == (0.0, 0.0, 0.0)
    assert fk[-1][0] > 1.0  # end-effector x coordinate > 1.0


def test_forward_kinematics_changes_when_joints_change():
    """Stage1 migration: changing joints moves end-effector."""
    from robot.safety.kinematics import forward_kinematics_6dof
    from robot.safety.models import Scene
    scene = Scene.from_json(str(BENCH / "simple_joint_move_001" / "scene.json"))
    fk_a = forward_kinematics_6dof(robot=scene.robot, joints=(0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
    fk_b = forward_kinematics_6dof(robot=scene.robot, joints=(0.5, 0.0, 0.0, 0.0, 0.0, 0.0))
    assert fk_a[-1] != fk_b[-1]


# ── Decision logic ────────────────────────────────────────────────────────

def test_make_decision_rejects_collision():
    """Stage1 migration: collision → reject."""
    from robot.safety.evaluator import make_decision
    from robot.safety.models import SafetyConfig
    config = SafetyConfig(min_clearance=0.05, manual_review_clearance=0.1, max_joint_delta=1.2,
                          num_interpolation_steps=40, check_self_collision=False)
    decision = make_decision(joint_limits_ok=True, collision_free=False,
                             min_clearance=-0.05, max_joint_delta=0.1, config=config)
    assert decision == "reject"


def test_make_decision_manual_review_for_low_clearance():
    """Stage1 migration: low clearance → manual_review."""
    from robot.safety.evaluator import make_decision
    from robot.safety.models import SafetyConfig
    config = SafetyConfig(min_clearance=0.05, manual_review_clearance=0.1, max_joint_delta=1.2,
                          num_interpolation_steps=40, check_self_collision=False)
    decision = make_decision(joint_limits_ok=True, collision_free=True,
                             min_clearance=0.08, max_joint_delta=0.1, config=config)
    assert decision == "manual_review"


def test_classify_risk_level_approve_is_low():
    """Stage1 migration: clean case → low risk."""
    from robot.safety.evaluator import classify_risk_level
    from robot.safety.models import SafetyConfig
    config = SafetyConfig(min_clearance=0.05, manual_review_clearance=0.1, max_joint_delta=1.2,
                          num_interpolation_steps=40, check_self_collision=False)
    risk = classify_risk_level(joint_limits_ok=True, collision_free=True,
                               min_clearance=0.2, max_joint_delta=0.1, config=config)
    assert risk == "low"


def test_check_joint_limits_reports_violation():
    """Stage1 migration: joint limits detection."""
    from robot.safety.models import Scene
    from robot.safety.evaluator import check_trajectory_joint_limits
    scene = Scene.from_json(str(BENCH / "obstacle_collision_001" / "scene.json"))
    trajectory = [(0.0, 0.0, 0.0, 0.0, 0.0, 0.0), (3.5, 0.0, 0.0, 0.0, 0.0, 0.0)]
    ok, violations = check_trajectory_joint_limits(trajectory=trajectory,
                                                   joint_limits=scene.robot.joint_limits)
    assert ok is False
    assert any(v.type == "joint_limit" for v in violations)


# ── Backend factory edge cases ────────────────────────────────────────────

def test_backend_factory_rejects_unknown():
    """Stage2 migration: unknown backend → ValueError."""
    from robot.backends.backend_factory import create_backend
    with pytest.raises(ValueError, match="unsupported"):
        create_backend("unknown")


def test_backend_factory_creates_pybullet():
    """Stage2 migration: pybullet backend creation (skipped if pybullet absent)."""
    pytest.importorskip("pybullet")
    from robot.backends.backend_factory import create_backend
    backend = create_backend("pybullet")
    assert backend.name == "pybullet"
