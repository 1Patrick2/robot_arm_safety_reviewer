"""Capability test: external trajectory pipeline — schema, loader, conversion, evidence."""

import json
from pathlib import Path


def test_external_trajectory_schema():
    from bench.adapters.external_trajectory import ExternalActionFrame, ExternalTrajectory, ActionMappingConfig
    frame = ExternalActionFrame(step_index=0, action=(0.1, 0.2), action_type="joint_position", source="test")
    traj = ExternalTrajectory(dataset_name="ds", episode_id="ep1", action_type="joint_position", frames=(frame,))
    assert traj.dataset_name == "ds"
    mapping = ActionMappingConfig(joint_count=2)
    assert mapping.joint_count == 2


def test_action_mapping_config_validation():
    from bench.adapters.external_trajectory import ActionMappingConfig
    import pytest
    with pytest.raises(ValueError, match="joint_count"):
        ActionMappingConfig(joint_count=0)
    with pytest.raises(ValueError, match="offset length"):
        ActionMappingConfig(joint_count=6, offset=(0.0, 0.0))
    with pytest.raises(ValueError, match="current_joints_policy"):
        ActionMappingConfig(joint_count=6, current_joints_policy="unknown")


def test_lerobot_style_loader(tmp_path):
    from bench.adapters.lerobot_episode_adapter import load_lerobot_style_episode
    p = tmp_path / "ep.json"
    p.write_text(json.dumps({
        "dataset_name": "test_ds", "episode_id": "ep001", "action_type": "joint_position",
        "actions": [[0.1, 0.2], [0.3, 0.4]], "timestamps": [0.0, 0.1],
    }), encoding="utf-8")
    traj = load_lerobot_style_episode(p)
    assert len(traj.frames) == 2


def test_lerobot_loader_missing_fields_raise(tmp_path):
    from bench.adapters.lerobot_episode_adapter import load_lerobot_style_episode
    import pytest
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"action_type": "joint_position", "actions": [[0.1]]}), encoding="utf-8")
    with pytest.raises(ValueError, match="dataset_name"):
        load_lerobot_style_episode(p)


def test_external_trajectory_conversion():
    from bench.adapters.external_trajectory import (
        ExternalActionFrame, ExternalTrajectory, ActionMappingConfig,
        external_trajectory_to_policy_sequence,
    )
    traj = ExternalTrajectory(
        dataset_name="test", episode_id="ep1", action_type="joint_position",
        frames=(ExternalActionFrame(0, (0.1, 0.2, 0.0, 0.0, 0.0, 0.0), "joint_position", "test"),),
    )
    mapping = ActionMappingConfig(joint_count=6)
    seq = external_trajectory_to_policy_sequence(traj, mapping)
    assert seq.sequence_id == "test__ep1"
    assert len(seq.actions) == 1


def test_external_trajectory_evidence(tmp_path):
    from diagnostics.evidence.external_trajectory import ExternalTrajectoryRecord, write_external_trajectory_record
    from diagnostics.evidence.manifest import build_evidence_manifest
    rec = ExternalTrajectoryRecord(dataset_name="ds", episode_id="ep1", action_type="joint_position", frame_count=2, source_path="/m", sequence_id="s1")
    rec_path = tmp_path / "ext.json"
    write_external_trajectory_record(rec, rec_path)
    ctx = tmp_path / "ctx.json"
    ctx.write_text(json.dumps({"episode_id": "ep_ext", "artifacts": []}), encoding="utf-8")
    manifest = build_evidence_manifest(context_path=ctx, external_trajectory_record_path=rec_path)
    assert manifest["checks"]["has_external_trajectory_evidence"] is True
    assert manifest["evidence_groups"]["external_trajectory"]["available"] is True


def test_external_trajectory_contract(tmp_path):
    from diagnostics.evidence.external_trajectory import ExternalTrajectoryRecord, write_external_trajectory_record
    from diagnostics.evidence.manifest import build_evidence_manifest
    from diagnostics.contracts.expected import validate_expected_contract
    rec = ExternalTrajectoryRecord(dataset_name="ds", episode_id="ep1", action_type="joint_position", frame_count=2, source_path="/m", sequence_id="s1")
    rec_path = tmp_path / "ext.json"
    write_external_trajectory_record(rec, rec_path)
    ctx = tmp_path / "ctx.json"
    ctx.write_text(json.dumps({"episode_id": "ep_ct", "artifacts": []}), encoding="utf-8")
    manifest = build_evidence_manifest(context_path=ctx, external_trajectory_record_path=rec_path)
    actual = {"total_steps": 1}
    expected = {"required_artifacts": ["external_trajectory_record", "evidence_manifest"], "required_evidence_groups": ["external_trajectory"]}
    passed, errors = validate_expected_contract(expected=expected, actual=actual, manifest=manifest)
    assert passed is True, f"errors={errors}"
