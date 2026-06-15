import json
from pathlib import Path

from application.dataset_service import (
    DatasetExportSequenceRequest,
    DatasetListRequest,
    dataset_export_sequence,
    dataset_list,
)
from application.sequence_runtime_service import SequenceRuntimeRequest, run_sequence_runtime

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"
LEROY_SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "lerobot_style"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"


def test_dataset_list_then_sequence_runtime(tmp_path):
    """Verify that a sequence discovered via mini adapter can be run through the runtime."""

    # 1. list sequences via adapter
    list_result = dataset_list(
        DatasetListRequest(
            adapter_name="mini_sequence",
            source=SAMPLES,
        )
    )
    assert "simple_safe_sequence_001" in list_result.sequence_ids

    # 2. export the sequence to a temp file
    export_output = tmp_path / "exported_sequence.json"
    export_result = dataset_export_sequence(
        DatasetExportSequenceRequest(
            adapter_name="mini_sequence",
            source=SAMPLES,
            sequence_id="simple_safe_sequence_001",
            output=export_output,
        )
    )
    assert export_result.exported_path == export_output
    assert export_output.exists()

    # 3. run the exported sequence through the sequence runtime
    runtime_result = run_sequence_runtime(
        SequenceRuntimeRequest(
            sequence_path=export_output,
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            episode_root=tmp_path / "runtime_output",
        )
    )

    # 4. verify runtime output
    assert runtime_result.sequence_id == "simple_safe_sequence_001"
    assert runtime_result.total_steps == 2
    assert runtime_result.executed_steps == 2
    assert runtime_result.approved_steps == 2
    assert runtime_result.blocked_steps == 0
    assert runtime_result.episode_dir.exists()
    assert (runtime_result.episode_dir / "steps.jsonl").exists()


def test_lerobot_style_dataset_then_sequence_runtime(tmp_path):
    """Verify that a lerobot_style episode can be exported and run through the runtime."""

    # 1. export the lerobot_style episode
    export_output = tmp_path / "exported_lerobot.json"
    export_result = dataset_export_sequence(
        DatasetExportSequenceRequest(
            adapter_name="lerobot_style",
            source=LEROY_SAMPLES,
            sequence_id="episode_000001",
            output=export_output,
        )
    )
    assert export_result.exported_path == export_output
    assert export_output.exists()

    # 2. run the exported sequence through the sequence runtime
    runtime_result = run_sequence_runtime(
        SequenceRuntimeRequest(
            sequence_path=export_output,
            scene_path=BENCH / "simple_joint_move_001" / "scene.json",
            backend_name="mock",
            episode_root=tmp_path / "runtime_output",
        )
    )

    # 3. verify runtime output
    assert runtime_result.sequence_id == "episode_000001"
    assert runtime_result.total_steps == 2
    assert runtime_result.executed_steps == 2
    assert runtime_result.approved_steps == 2
    assert runtime_result.blocked_steps == 0
    assert runtime_result.episode_dir.exists()
    assert (runtime_result.episode_dir / "steps.jsonl").exists()
