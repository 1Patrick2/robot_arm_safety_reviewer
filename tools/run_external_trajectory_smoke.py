"""Run external trajectory smoke: load, convert, evaluate, build manifest.

Usage:
    python tools/run_external_trajectory_smoke.py ^
      --episode bench/external_trajectory_smoke/lerobot_style_episode.json ^
      --mapping bench/external_trajectory_smoke/mapping_config.json ^
      --scene bench/external_trajectory_smoke/scene.json ^
      --out artifacts/external_trajectory_smoke
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run external trajectory smoke")
    parser.add_argument("--episode", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--backend", default="mock")
    parser.add_argument("--expected-contract")
    args = parser.parse_args()

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

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # Load
    traj = load_lerobot_style_episode(args.episode)
    mapping_data = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
    mapping_cfg = ActionMappingConfig(**mapping_data)
    seq = external_trajectory_to_policy_sequence(traj, mapping_cfg)

    # Write converted sequence
    seq_path = out / "converted_sequence.json"
    seq_path.write_text(json.dumps({
        "sequence_id": seq.sequence_id,
        "source": seq.source,
        "initial_joints": list(seq.initial_joints),
        "actions": [{"action_type": a.action_type, "values": list(a.values), "timestamp": a.timestamp}
                     for a in seq.actions],
    }, indent=2), encoding="utf-8")
    print(f"  Written: {seq_path}")

    # Run sandbox
    from application.sandbox_service import SandboxRunRequest, run_sandbox  # noqa: PLC0415
    sandbox_result = run_sandbox(SandboxRunRequest(
        sequence_path=seq_path,
        scene_path=Path(args.scene),
        backend_name=args.backend,
        output_root=out / "sandbox",
        stop_on_block=False,
    ))
    runtime = sandbox_result.sequence_runtime_result

    # Write external trajectory record
    ext_rec = ExternalTrajectoryRecord(
        dataset_name=traj.dataset_name,
        episode_id=traj.episode_id,
        robot_name=traj.robot_name,
        action_type=traj.action_type,
        frame_count=len(traj.frames),
        mapping=mapping_data,
        source_path=str(Path(args.episode).resolve()),
        sequence_id=seq.sequence_id,
    )
    rec_path = out / "external_trajectory_record.json"
    write_external_trajectory_record(ext_rec, rec_path)
    print(f"  Written: {rec_path}")

    # Build context and manifest
    ctx = out / "diagnostic_context.json"
    ctx.write_text(json.dumps({
        "episode_id": runtime.episode_dir.name,
        "total_steps": runtime.total_steps,
        "approved_steps": runtime.approved_steps,
        "rejected_steps": runtime.rejected_steps,
        "manual_review_steps": runtime.manual_review_steps,
        "artifacts": [],
    }), encoding="utf-8")

    manifest = build_evidence_manifest(context_path=ctx, external_trajectory_record_path=rec_path)
    manifest_path = out / "evidence_manifest.json"
    write_evidence_manifest(manifest, manifest_path)
    print(f"  Written: {manifest_path}")

    # Contract validation
    contract_passed = None
    if args.expected_contract:
        contract = json.loads(Path(args.expected_contract).read_text(encoding="utf-8"))
        actual = {"total_steps": runtime.total_steps}
        cp, errors = validate_expected_contract(expected=contract["expected"], actual=actual, manifest=manifest)
        contract_passed = cp
        print(f"  Expected contract: {'PASS' if cp else 'FAIL'}")
        if errors:
            print(f"  Errors: {errors}")

    # Summary
    summary = [
        f"# External Trajectory Smoke Summary",
        f"",
        f"- Dataset: {traj.dataset_name}",
        f"- Episode: {traj.episode_id}",
        f"- Robot: {traj.robot_name or 'N/A'}",
        f"- Action Type: {traj.action_type}",
        f"- Frame Count: {len(traj.frames)}",
        f"- Sequence: {seq.sequence_id}",
        f"- Total Steps: {runtime.total_steps}",
        f"- Approved: {runtime.approved_steps}",
        f"- Rejected: {runtime.rejected_steps}",
        f"- Manual Review: {runtime.manual_review_steps}",
        f"- External Trajectory Evidence: {manifest['checks']['has_external_trajectory_evidence']}",
        f"- External Trajectory Record Valid: {manifest['checks']['external_trajectory_record_valid']}",
    ]
    if contract_passed is not None:
        summary.append(f"- Expected Contract: {'PASS' if contract_passed else 'FAIL'}")
    summary_path = out / "summary.md"
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(f"  Written: {summary_path}")
    print(f"\n  Done. Output in: {out}")


if __name__ == "__main__":
    main()
