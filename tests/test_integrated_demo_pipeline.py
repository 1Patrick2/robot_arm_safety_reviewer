"""Capability test: integrated demo pipeline — fake full chain."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE_DIR = ROOT / "bench" / "external_trajectory_smoke"


def test_fake_integrated_demo_produces_all_artifacts(tmp_path):
    from bench.adapters.lerobot_episode_adapter import load_lerobot_style_episode
    from bench.adapters.external_trajectory import ActionMappingConfig, external_trajectory_to_policy_sequence
    from application.sandbox_service import SandboxRunRequest, run_sandbox
    from diagnostics.evidence.external_trajectory import ExternalTrajectoryRecord, write_external_trajectory_record
    from diagnostics.evidence.manifest import build_evidence_manifest, write_evidence_manifest
    from diagnostics.analysis.final_answer import generate_fake_final_answer, write_final_answer

    traj = load_lerobot_style_episode(SMOKE_DIR / "lerobot_style_episode.json")
    mapping = json.loads((SMOKE_DIR / "mapping_config.json").read_text(encoding="utf-8"))
    seq = external_trajectory_to_policy_sequence(traj, ActionMappingConfig(**mapping))

    seq_path = tmp_path / "converted_sequence.json"
    seq_path.write_text(json.dumps({"sequence_id": seq.sequence_id, "source": seq.source, "initial_joints": list(seq.initial_joints),
        "actions": [{"action_type": a.action_type, "values": list(a.values), "timestamp": a.timestamp} for a in seq.actions]}), encoding="utf-8")

    sb = run_sandbox(SandboxRunRequest(sequence_path=seq_path, scene_path=SMOKE_DIR / "scene.json", backend_name="mock", output_root=tmp_path / "sandbox", stop_on_block=False))
    r = sb.sequence_runtime_result

    rec = ExternalTrajectoryRecord(dataset_name=traj.dataset_name, episode_id=traj.episode_id, robot_name=traj.robot_name,
        action_type=traj.action_type, frame_count=len(traj.frames), mapping=mapping, source_path=str(SMOKE_DIR / "lerobot_style_episode.json"), sequence_id=seq.sequence_id)
    rec_path = tmp_path / "external_trajectory_record.json"
    write_external_trajectory_record(rec, rec_path)

    ctx = tmp_path / "diagnostic_context.json"
    ctx.write_text(json.dumps({"episode_id": r.episode_dir.name, "total_steps": r.total_steps, "approved_steps": r.approved_steps,
        "rejected_steps": r.rejected_steps, "manual_review_steps": r.manual_review_steps, "artifacts": []}), encoding="utf-8")
    manifest = build_evidence_manifest(context_path=ctx, external_trajectory_record_path=rec_path)

    answer = generate_fake_final_answer(fused_decision="approve", dataset_name=traj.dataset_name)
    ans_path = tmp_path / "llm_diagnostic_analysis.json"
    write_final_answer(answer, ans_path)

    assert seq_path.exists()
    assert rec_path.exists()
    assert ctx.exists()
    assert ans_path.exists()
    assert manifest["checks"]["has_external_trajectory_evidence"] is True
    assert manifest["evidence_groups"]["external_trajectory"]["available"] is True
    assert answer.advisory_decision == "approve"
    assert "advisory only" in answer.limitations[0]
