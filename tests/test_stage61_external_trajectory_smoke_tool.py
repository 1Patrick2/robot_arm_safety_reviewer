"""Test for the external trajectory smoke runner tool."""

import json
from pathlib import Path

SMOKE_DIR = Path(__file__).resolve().parents[1] / "bench" / "external_trajectory_smoke"


def test_smoke_tool_produces_expected_artifacts(tmp_path):
    """Run the smoke tool logic as a callable function and verify outputs."""
    from bench.adapters.lerobot_episode_adapter import load_lerobot_style_episode  # noqa: PLC0415
    from bench.adapters.external_trajectory import (  # noqa: PLC0415
        ActionMappingConfig,
        external_trajectory_to_policy_sequence,
    )
    from diagnostics.evidence.external_trajectory import (  # noqa: PLC0415
        ExternalTrajectoryRecord,
        write_external_trajectory_record,
    )
    from diagnostics.evidence.manifest import (  # noqa: PLC0415
        build_evidence_manifest,
        write_evidence_manifest,
    )
    from diagnostics.contracts.expected import validate_expected_contract  # noqa: PLC0415
    from application.sandbox_service import SandboxRunRequest, run_sandbox  # noqa: PLC0415

    out = tmp_path / "smoke_out"

    # Load
    traj = load_lerobot_style_episode(SMOKE_DIR / "lerobot_style_episode.json")
    mapping_data = json.loads((SMOKE_DIR / "mapping_config.json").read_text(encoding="utf-8"))
    mapping_cfg = ActionMappingConfig(**mapping_data)
    seq = external_trajectory_to_policy_sequence(traj, mapping_cfg)

    # Write sequence
    seq_path = out / "converted_sequence.json"
    seq_path.parent.mkdir(parents=True, exist_ok=True)
    seq_path.write_text(json.dumps({
        "sequence_id": seq.sequence_id,
        "source": seq.source,
        "initial_joints": list(seq.initial_joints),
        "actions": [{"action_type": a.action_type, "values": list(a.values), "timestamp": a.timestamp}
                     for a in seq.actions],
    }, indent=2), encoding="utf-8")

    # Run sandbox
    sb_result = run_sandbox(SandboxRunRequest(
        sequence_path=seq_path,
        scene_path=SMOKE_DIR / "scene.json",
        backend_name="mock",
        output_root=out / "sandbox",
        stop_on_block=False,
    ))
    runtime = sb_result.sequence_runtime_result

    # Write record
    ext_rec = ExternalTrajectoryRecord(
        dataset_name=traj.dataset_name, episode_id=traj.episode_id,
        robot_name=traj.robot_name, action_type=traj.action_type,
        frame_count=len(traj.frames), mapping=mapping_data,
        source_path=str(SMOKE_DIR / "lerobot_style_episode.json"),
        sequence_id=seq.sequence_id,
    )
    rec_path = out / "external_trajectory_record.json"
    write_external_trajectory_record(ext_rec, rec_path)

    # Build manifest
    ctx = out / "diagnostic_context.json"
    ctx.write_text(json.dumps({
        "episode_id": runtime.episode_dir.name, "total_steps": runtime.total_steps,
        "approved_steps": runtime.approved_steps, "rejected_steps": runtime.rejected_steps,
        "manual_review_steps": runtime.manual_review_steps, "artifacts": [],
    }), encoding="utf-8")
    manifest = build_evidence_manifest(context_path=ctx, external_trajectory_record_path=rec_path)
    manifest_path = out / "evidence_manifest.json"
    write_evidence_manifest(manifest, manifest_path)

    # Verify artifacts
    assert seq_path.exists()
    assert rec_path.exists()
    assert ctx.exists()
    assert manifest_path.exists()
    assert (out / "summary.md").exists() is False  # summary is only in CLI mode

    # Verify manifest
    assert manifest["checks"]["has_external_trajectory_evidence"] is True
    assert manifest["checks"]["external_trajectory_record_valid"] is True
    assert manifest["evidence_groups"]["external_trajectory"]["available"] is True
    assert any(a["kind"] == "external_trajectory_record" for a in manifest["artifacts"])

    # Verify contract
    contract = json.loads((SMOKE_DIR / "expected_contract.json").read_text(encoding="utf-8"))
    actual = {"total_steps": runtime.total_steps}
    cp, errors = validate_expected_contract(expected=contract["expected"], actual=actual, manifest=manifest)
    assert cp is True, f"Contract failed: {errors}"
