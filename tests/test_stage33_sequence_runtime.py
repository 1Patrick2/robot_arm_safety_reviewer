import json
import subprocess
import sys
from pathlib import Path

from application.sequence_runtime_service import SequenceRuntimeRequest, run_sequence_runtime


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"
SAMPLES = ROOT / "bench" / "samples" / "policy_sequences"


def _write_sequence(path: Path, *, sequence_id: str, actions: list[dict]) -> Path:
    path.write_text(
        json.dumps(
            {
                "sequence_id": sequence_id,
                "source": "unit_test",
                "initial_joints": [0, 0, 0, 0, 0, 0],
                "actions": actions,
            }
        ),
        encoding="utf-8",
    )
    return path


def test_sequence_runtime_executes_safe_sequence(tmp_path):
    result = run_sequence_runtime(
        SequenceRuntimeRequest(
            sequence_path=SAMPLES / "simple_safe_sequence.json",
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            episode_root=tmp_path,
        )
    )

    payload = result.to_dict()

    assert payload["sequence_id"] == "simple_safe_sequence_001"
    assert payload["total_steps"] == 2
    assert payload["approved_steps"] == 2
    assert payload["executed_steps"] == 2
    assert payload["blocked_steps"] == 0
    assert [step.safety_result.decision for step in result.step_results] == ["approve", "approve"]
    assert [step.step_index for step in result.step_results] == [1, 2]
    assert result.episode_dir.exists()
    assert (result.episode_dir / "steps.jsonl").read_text(encoding="utf-8").count("\n") == 2


def test_sequence_runtime_blocks_collision_sequence(tmp_path):
    result = run_sequence_runtime(
        SequenceRuntimeRequest(
            sequence_path=SAMPLES / "collision_sequence.json",
            scene_path=BENCH / "obstacle_collision_001" / "scene.json",
            backend_name="mock",
            episode_root=tmp_path,
        )
    )

    step = result.step_results[0]

    assert result.total_steps == 1
    assert result.approved_steps == 0
    assert result.executed_steps == 0
    assert result.blocked_steps == 1
    assert result.rejected_steps == 1
    assert step.safety_result.decision == "reject"
    assert step.executed is False
    assert step.sent_action is None
    assert step.blocked_reason == "rejected_by_safety_gate"


def test_sequence_runtime_blocks_manual_review_sequence(tmp_path):
    sequence_path = _write_sequence(
        tmp_path / "manual_review_sequence.json",
        sequence_id="manual_review_sequence_001",
        actions=[
            {
                "action_type": "joint_target",
                "values": [0, 0.1, -0.1, 0, 0, 0],
            }
        ],
    )
    result = run_sequence_runtime(
        SequenceRuntimeRequest(
            sequence_path=sequence_path,
            scene_path=BENCH / "near_miss_clearance_001" / "scene.json",
            backend_name="mock",
            episode_root=tmp_path,
        )
    )

    assert result.executed_steps == 0
    assert result.approved_steps == 0
    assert result.manual_review_steps == 1
    assert result.blocked_steps == 1
    assert result.step_results[0].safety_result.decision == "manual_review"
    assert result.step_results[0].blocked_reason == "manual_review_required"


def test_sequence_runtime_continue_on_block_records_remaining_steps(tmp_path):
    result = run_sequence_runtime(
        SequenceRuntimeRequest(
            sequence_path=SAMPLES / "near_miss_sequence.json",
            scene_path=BENCH / "near_miss_clearance_001" / "scene.json",
            backend_name="mock",
            episode_root=tmp_path,
            stop_on_block=False,
        )
    )

    assert result.total_steps == 2
    assert result.executed_steps == 0
    assert result.blocked_steps == 2
    assert [step.step_index for step in result.step_results] == [1, 2]


def test_sequence_runtime_to_app_result_contains_episode_artifact(tmp_path):
    result = run_sequence_runtime(
        SequenceRuntimeRequest(
            sequence_path=SAMPLES / "simple_safe_sequence.json",
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            episode_root=tmp_path,
        )
    )

    app_result = result.to_app_result()

    assert app_result.ok is True
    assert app_result.mode == "sequence_runtime"
    assert app_result.artifacts[0].kind == "runtime_episode"
    assert app_result.artifacts[0].path == result.episode_dir


def test_sequence_cli_smoke_json(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "sequence",
            "run",
            "--sequence",
            str(SAMPLES / "simple_safe_sequence.json"),
            "--scene",
            str(BENCH / "simple_joint_move_001" / "scene.json"),
            "--backend",
            "mock",
            "--episode-root",
            str(tmp_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["sequence_id"] == "simple_safe_sequence_001"
    assert payload["total_steps"] == 2
    assert payload["approved_steps"] == 2
    assert payload["executed_steps"] == 2
    assert Path(payload["episode_dir"]).exists()


def test_sequence_cli_continue_on_block_json(tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "sequence",
            "run",
            "--sequence",
            str(SAMPLES / "near_miss_sequence.json"),
            "--scene",
            str(BENCH / "near_miss_clearance_001" / "scene.json"),
            "--backend",
            "mock",
            "--episode-root",
            str(tmp_path),
            "--continue-on-block",
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["total_steps"] == 2
    assert payload["approved_steps"] == 0
    assert payload["blocked_steps"] == 2
