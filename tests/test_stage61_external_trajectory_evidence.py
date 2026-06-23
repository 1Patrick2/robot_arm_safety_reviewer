import json
from pathlib import Path

from bench.adapters.external_trajectory import ActionMappingConfig
from bench.adapters.lerobot_episode_adapter import load_lerobot_style_episode
from bench.adapters.external_trajectory import external_trajectory_to_policy_sequence
from diagnostics.evidence.external_trajectory import (
    ExternalTrajectoryRecord,
    write_external_trajectory_record,
)
from diagnostics.evidence.manifest import build_evidence_manifest
from diagnostics.contracts.expected import validate_expected_contract


SMOKE_DIR = Path(__file__).resolve().parents[1] / "bench" / "external_trajectory_smoke"


class TestExternalTrajectoryEvidence:
    def test_evidence_record_writes_json(self, tmp_path):
        rec = ExternalTrajectoryRecord(
            dataset_name="ds", episode_id="ep1", action_type="joint_position",
            frame_count=2, source_path="/mock", sequence_id="s1",
        )
        out = tmp_path / "ext.json"
        write_external_trajectory_record(rec, out)
        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["schema_version"] == "external_trajectory_record.v1"

    def test_manifest_includes_external_trajectory(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"episode_id": "ep_ext", "artifacts": []}), encoding="utf-8")
        rec = ExternalTrajectoryRecord(
            dataset_name="ds", episode_id="ep1", action_type="joint_position",
            frame_count=2, source_path="/m", sequence_id="s1",
        )
        rec_path = tmp_path / "ext.json"
        write_external_trajectory_record(rec, rec_path)
        manifest = build_evidence_manifest(context_path=ctx, external_trajectory_record_path=rec_path)
        assert manifest["checks"]["has_external_trajectory_evidence"] is True
        assert manifest["checks"]["external_trajectory_record_valid"] is True
        kinds = {a["kind"] for a in manifest["artifacts"]}
        assert "external_trajectory_record" in kinds

    def test_evidence_group_available(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"episode_id": "ep_eg", "artifacts": []}), encoding="utf-8")
        rec = ExternalTrajectoryRecord(
            dataset_name="ds", episode_id="ep1", action_type="joint_position",
            frame_count=2, source_path="/m", sequence_id="s1",
        )
        rec_path = tmp_path / "ext.json"
        write_external_trajectory_record(rec, rec_path)
        manifest = build_evidence_manifest(context_path=ctx, external_trajectory_record_path=rec_path)
        assert manifest["evidence_groups"]["external_trajectory"]["available"] is True

    def test_expected_contract_requires_external_trajectory(self, tmp_path):
        ctx = tmp_path / "ctx.json"
        ctx.write_text(json.dumps({"episode_id": "ep_ct", "artifacts": []}), encoding="utf-8")
        rec = ExternalTrajectoryRecord(
            dataset_name="ds", episode_id="ep1", action_type="joint_position",
            frame_count=2, source_path="/m", sequence_id="s1",
        )
        rec_path = tmp_path / "ext.json"
        write_external_trajectory_record(rec, rec_path)
        manifest = build_evidence_manifest(context_path=ctx, external_trajectory_record_path=rec_path)
        actual = {"total_steps": 1}
        expected = {
            "required_artifacts": ["external_trajectory_record", "evidence_manifest"],
            "required_evidence_groups": ["external_trajectory"],
        }
        passed, errors = validate_expected_contract(expected=expected, actual=actual, manifest=manifest)
        assert passed is True, f"Contract failed: {errors}"

    def test_smoke_fixture_end_to_end(self, tmp_path):
        """Load the smoke fixture, convert, run sandbox, build manifest, check contract."""
        from application.sandbox_service import SandboxRunRequest, run_sandbox  # noqa: PLC0415

        # Load external trajectory
        traj = load_lerobot_style_episode(SMOKE_DIR / "lerobot_style_episode.json")
        mapping = json.loads((SMOKE_DIR / "mapping_config.json").read_text(encoding="utf-8"))
        mapping_cfg = ActionMappingConfig(**mapping)
        seq = external_trajectory_to_policy_sequence(traj, mapping_cfg)

        # Write out converted sequence (so sandbox can read it)
        seq_path = tmp_path / "converted_sequence.json"
        seq_path.write_text(json.dumps({
            "sequence_id": seq.sequence_id,
            "source": seq.source,
            "initial_joints": list(seq.initial_joints),
            "actions": [
                {
                    "action_type": a.action_type,
                    "values": list(a.values),
                    "timestamp": a.timestamp,
                }
                for a in seq.actions
            ],
        }), encoding="utf-8")

        # Run sandbox
        sandbox_result = run_sandbox(SandboxRunRequest(
            sequence_path=seq_path,
            scene_path=SMOKE_DIR / "scene.json",
            backend_name="mock",
            output_root=tmp_path / "sandbox",
            stop_on_block=False,
        ))
        runtime = sandbox_result.sequence_runtime_result
        episode_dir = runtime.episode_dir

        # Build external trajectory record
        ext_rec = ExternalTrajectoryRecord(
            dataset_name=traj.dataset_name,
            episode_id=traj.episode_id,
            robot_name=traj.robot_name,
            action_type=traj.action_type,
            frame_count=len(traj.frames),
            mapping=mapping,
            source_path=str(SMOKE_DIR / "lerobot_style_episode.json"),
            sequence_id=seq.sequence_id,
        )
        ext_rec_path = tmp_path / "external_trajectory_record.json"
        write_external_trajectory_record(ext_rec, ext_rec_path)

        # Build context + manifest
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": runtime.episode_dir.name,
            "total_steps": runtime.total_steps,
            "approved_steps": runtime.approved_steps,
            "rejected_steps": runtime.rejected_steps,
            "manual_review_steps": runtime.manual_review_steps,
            "artifacts": [],
        }), encoding="utf-8")

        manifest = build_evidence_manifest(
            context_path=ctx,
            external_trajectory_record_path=ext_rec_path,
        )
        assert manifest["checks"]["has_external_trajectory_evidence"] is True
        assert manifest["evidence_groups"]["external_trajectory"]["available"] is True

        # Validate expected contract
        contract = json.loads((SMOKE_DIR / "expected_contract.json").read_text(encoding="utf-8"))
        actual = {"total_steps": runtime.total_steps}
        passed, errors = validate_expected_contract(
            expected=contract["expected"],
            actual=actual,
            manifest=manifest,
        )
        assert passed is True, f"Smoke contract failed: {errors}"
