"""Capability test: robot safety pipeline — scene, sequence, sandbox, runtime."""

import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "bench" / "samples" / "policy_sequences"
BENCH = ROOT / "bench" / "sim_robot_arm"


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
