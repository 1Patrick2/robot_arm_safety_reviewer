import json
from pathlib import Path

import pytest

from diagnostics.evidence.manifest import build_evidence_manifest, write_evidence_manifest


class TestBuildEvidenceManifest:
    def test_from_minimal_context(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_test",
            "sequence_id": "seq_test",
            "backend": "mock",
            "device": "mock_realman",
            "run_mode": "sequence_runtime",
            "total_steps": 2,
            "approved_steps": 2,
            "executed_steps": 2,
            "blocked_steps": 0,
            "rejected_steps": 0,
            "manual_review_steps": 0,
            "min_clearance": 0.5,
            "worst_sequence_step_index": 1,
            "backend_worst_step": 3,
            "closest_robot_link": "link_2",
            "closest_obstacle": "obs_1",
            "artifacts": [],
        }), encoding="utf-8")

        manifest = build_evidence_manifest(context_path=ctx)

        assert manifest["schema_version"] == "evidence_manifest.v1"
        assert manifest["episode_id"] == "ep_test"
        assert manifest["summary"]["total_steps"] == 2
        assert manifest["checks"]["has_diagnostic_context"] is True

    def test_existing_artifact_file(self, tmp_path):
        existing = tmp_path / "trajectory_overview.png"
        existing.write_text("fake-png", encoding="utf-8")

        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_art",
            "artifacts": [
                {"kind": "trajectory_overview", "path": str(existing)},
            ],
        }), encoding="utf-8")

        manifest = build_evidence_manifest(context_path=ctx)
        art_paths = [(a["kind"], a["exists"]) for a in manifest["artifacts"]]
        assert ("trajectory_overview", True) in art_paths
        assert manifest["checks"]["has_visual_evidence"] is True

    def test_missing_artifact_does_not_crash(self, tmp_path):
        missing = tmp_path / "nonexistent.png"

        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_miss",
            "artifacts": [
                {"kind": "trajectory_overview", "path": str(missing)},
            ],
        }), encoding="utf-8")

        manifest = build_evidence_manifest(context_path=ctx)
        art = [a for a in manifest["artifacts"] if a["kind"] == "trajectory_overview"][0]
        assert art["exists"] is False

    def test_with_all_reports(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_full",
            "artifacts": [],
        }), encoding="utf-8")

        report = tmp_path / "diagnostic_report.md"
        report.write_text("# Report", encoding="utf-8")

        trace = tmp_path / "diagnostic_runtime_trace.json"
        trace.write_text(json.dumps({"has_violations": True}), encoding="utf-8")

        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        agent_report = agent_dir / "diagnostic_agent_report.md"
        agent_report.write_text("# Agent", encoding="utf-8")

        manifest = build_evidence_manifest(
            context_path=ctx,
            deterministic_report_path=report,
            agent_report_path=agent_report,
            trace_path=trace,
        )

        checks = manifest["checks"]
        assert checks["has_diagnostic_report"] is True
        assert checks["has_trace"] is True
        assert checks["has_agent_report"] is True
        assert checks["has_guardrail_violations"] is True

    def test_non_dict_json_raises(self, tmp_path):
        ctx = tmp_path / "bad_context.json"
        ctx.write_text(json.dumps([1, 2, 3]), encoding="utf-8")

        with pytest.raises(ValueError, match="must be a JSON object"):
            build_evidence_manifest(context_path=ctx)

    def test_missing_context_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            build_evidence_manifest(context_path=tmp_path / "nonexistent.json")

    def test_context_markdown_included(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_md",
            "artifacts": [],
        }), encoding="utf-8")

        ctx_md = tmp_path / "diagnostic_context.md"
        ctx_md.write_text("# Context", encoding="utf-8")

        manifest = build_evidence_manifest(context_path=ctx)
        kinds = {a["kind"] for a in manifest["artifacts"]}
        assert "diagnostic_context_markdown" in kinds


    def test_missing_report_path_sets_check_false(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_missing_report",
            "artifacts": [],
        }), encoding="utf-8")

        missing_report = tmp_path / "nonexistent" / "diagnostic_report.md"
        manifest = build_evidence_manifest(
            context_path=ctx,
            deterministic_report_path=missing_report,
        )
        rep_artifacts = [a for a in manifest["artifacts"] if a["kind"] == "deterministic_report"]
        assert len(rep_artifacts) == 1
        assert rep_artifacts[0]["exists"] is False
        assert manifest["checks"]["has_diagnostic_report"] is False

    def test_missing_visual_artifact_sets_visual_check_false(self, tmp_path):
        missing_vis = tmp_path / "nonexistent_trajectory.png"
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_missing_vis",
            "artifacts": [
                {"kind": "trajectory_overview", "path": str(missing_vis)},
            ],
        }), encoding="utf-8")

        manifest = build_evidence_manifest(context_path=ctx)
        vis_artifacts = [a for a in manifest["artifacts"] if a["kind"] == "trajectory_overview"]
        assert len(vis_artifacts) == 1
        assert vis_artifacts[0]["exists"] is False
        assert manifest["checks"]["has_visual_evidence"] is False

    def test_only_episode_summary_does_not_count_as_visual_evidence(self, tmp_path):
        """episode_summary alone should not set has_visual_evidence to True."""
        summary_path = tmp_path / "episode_summary.md"
        summary_path.write_text("# Summary", encoding="utf-8")

        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_summary_only",
            "artifacts": [
                {"kind": "episode_summary", "path": str(summary_path)},
            ],
        }), encoding="utf-8")

        manifest = build_evidence_manifest(context_path=ctx)
        assert manifest["checks"]["has_visual_evidence"] is False

    def test_corrupted_trace_sets_trace_valid_false(self, tmp_path):
        """Corrupted trace JSON should not be silently treated as 'no violations'."""
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_corrupt_trace",
            "artifacts": [],
        }), encoding="utf-8")

        bad_trace = tmp_path / "bad_trace.json"
        bad_trace.write_text("not valid json", encoding="utf-8")

        manifest = build_evidence_manifest(
            context_path=ctx,
            trace_path=bad_trace,
        )
        assert manifest["trace_valid"] is False
        assert manifest["checks"]["has_guardrail_violations"] is False

    def test_manifest_contains_evidence_groups(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_groups",
            "total_steps": 2,
            "approved_steps": 2,
            "executed_steps": 2,
            "blocked_steps": 0,
            "rejected_steps": 0,
            "manual_review_steps": 0,
            "artifacts": [],
        }), encoding="utf-8")

        report = tmp_path / "diagnostic_report.md"
        report.write_text("# R", encoding="utf-8")
        trace = tmp_path / "diagnostic_runtime_trace.json"
        trace.write_text("{}", encoding="utf-8")

        manifest = build_evidence_manifest(
            context_path=ctx,
            deterministic_report_path=report,
            trace_path=trace,
        )
        groups = manifest.get("evidence_groups")
        assert groups is not None
        expected_groups = {"runtime", "safety", "geometry", "visual", "structured_visual", "diagnostic", "agent"}
        assert set(groups.keys()) == expected_groups
        for gname in expected_groups:
            g = groups[gname]
            assert "available" in g
            assert "summary_fields" in g
            assert "artifact_kinds" in g
            assert "evidence_refs" in g

    def test_structured_visual_group_available_when_data_exists(self, tmp_path):
        traj_data = tmp_path / "trajectory_overview_data.json"
        traj_data.write_text("{}", encoding="utf-8")

        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_struct_vis",
            "artifacts": [
                {"kind": "trajectory_overview_data", "path": str(traj_data)},
            ],
        }), encoding="utf-8")

        manifest = build_evidence_manifest(context_path=ctx)
        assert manifest["evidence_groups"]["structured_visual"]["available"] is True

    def test_agent_group_unavailable_without_agent_report(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_no_agent",
            "artifacts": [],
        }), encoding="utf-8")

        manifest = build_evidence_manifest(context_path=ctx)
        assert manifest["evidence_groups"]["agent"]["available"] is False

    def test_agent_group_available_with_agent_report(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_agent",
            "artifacts": [],
        }), encoding="utf-8")

        agent_dir = tmp_path / "agent"
        agent_dir.mkdir()
        agent_report = agent_dir / "diagnostic_agent_report.md"
        agent_report.write_text("# Agent", encoding="utf-8")

        manifest = build_evidence_manifest(
            context_path=ctx,
            agent_report_path=agent_report,
        )
        assert manifest["checks"]["has_agent_report"] is True
        assert manifest["evidence_groups"]["agent"]["available"] is True

    def test_safety_group_refs_include_context_report_trace(self, tmp_path):
        ctx = tmp_path / "diagnostic_context.json"
        ctx.write_text(json.dumps({
            "episode_id": "ep_safety_refs",
            "artifacts": [],
        }), encoding="utf-8")
        report = tmp_path / "diagnostic_report.md"
        report.write_text("# R", encoding="utf-8")
        trace = tmp_path / "diagnostic_runtime_trace.json"
        trace.write_text("{}", encoding="utf-8")

        manifest = build_evidence_manifest(
            context_path=ctx,
            deterministic_report_path=report,
            trace_path=trace,
        )
        refs = manifest["evidence_groups"]["safety"]["evidence_refs"]
        assert "artifacts.diagnostic_context_json" in refs
        assert "artifacts.deterministic_report" in refs
        assert "artifacts.diagnostic_runtime_trace" in refs


class TestWriteEvidenceManifest:
    def test_writes_json(self, tmp_path):
        manifest = {"schema_version": "evidence_manifest.v1", "episode_id": "ep_w"}
        out = tmp_path / "nested" / "manifest.json"
        result = write_evidence_manifest(manifest, out)
        assert result == out
        assert out.exists()
        loaded = json.loads(out.read_text(encoding="utf-8"))
        assert loaded["episode_id"] == "ep_w"
