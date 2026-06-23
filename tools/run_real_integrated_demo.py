"""Run the full integrated demo: external trajectory → safety → perception → LLM → final answer.

Usage with fake LLM (no API key required):
    PYTHONPATH=. python tools/run_real_integrated_demo.py ^
      --episode bench/external_trajectory_smoke/lerobot_style_episode.json ^
      --mapping bench/external_trajectory_smoke/mapping_config.json ^
      --scene bench/external_trajectory_smoke/scene.json ^
      --llm-provider fake ^
      --out artifacts/real_integrated_demo

Usage with real YOLO + real LLM:
    PYTHONPATH=. python tools/run_real_integrated_demo.py ^
      --episode bench/external_trajectory_smoke/lerobot_style_episode.json ^
      --mapping bench/external_trajectory_smoke/mapping_config.json ^
      --scene bench/external_trajectory_smoke/scene.json ^
      --yolo-model local_data/real_perception_smoke/yolo26n.onnx ^
      --image local_data/real_perception_smoke/bus.jpg ^
      --llm-provider deepseek ^
      --llm-model deepseek-chat ^
      --out artifacts/real_integrated_demo
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Real integrated demo runner")
    parser.add_argument("--episode", required=True)
    parser.add_argument("--mapping", required=True)
    parser.add_argument("--scene", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--backend", default="mock")
    parser.add_argument("--yolo-model")
    parser.add_argument("--image")
    parser.add_argument("--llm-provider", default="fake")
    parser.add_argument("--llm-model", default="deepseek-chat")
    parser.add_argument("--expected-contract")
    parser.add_argument("--skip-yolo", action="store_true")
    parser.add_argument("--skip-llm", action="store_true")
    args = parser.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    # --- Imports (lazy to avoid startup failures) ---
    from bench.adapters.lerobot_episode_adapter import load_lerobot_style_episode  # noqa: PLC0415
    from bench.adapters.external_trajectory import (  # noqa: PLC0415
        ActionMappingConfig, external_trajectory_to_policy_sequence,
    )
    from diagnostics.evidence.external_trajectory import (  # noqa: PLC0415
        ExternalTrajectoryRecord, write_external_trajectory_record,
    )
    from diagnostics.evidence.manifest import (  # noqa: PLC0415
        build_evidence_manifest, write_evidence_manifest,
    )
    from diagnostics.analysis.final_answer import (  # noqa: PLC0415
        LLMFinalAnswer, generate_fake_final_answer, write_final_answer,
    )
    from application.sandbox_service import SandboxRunRequest, run_sandbox  # noqa: PLC0415

    # --- Step 1: Load external trajectory and convert ---
    print("[1/6] Loading external trajectory...")
    traj = load_lerobot_style_episode(args.episode)
    mapping_data = json.loads(Path(args.mapping).read_text(encoding="utf-8"))
    mapping_cfg = ActionMappingConfig(**mapping_data)
    seq = external_trajectory_to_policy_sequence(traj, mapping_cfg)

    seq_path = out / "converted_sequence.json"
    seq_path.write_text(json.dumps({
        "sequence_id": seq.sequence_id, "source": seq.source,
        "initial_joints": list(seq.initial_joints),
        "actions": [{"action_type": a.action_type, "values": list(a.values), "timestamp": a.timestamp}
                     for a in seq.actions],
    }, indent=2), encoding="utf-8")
    print(f"  -> {seq_path}")

    # --- Step 2: Run sandbox ---
    print("[2/6] Running safety runtime...")
    sandbox_result = run_sandbox(SandboxRunRequest(
        sequence_path=seq_path, scene_path=Path(args.scene),
        backend_name=args.backend, output_root=out / "sandbox",
        stop_on_block=False,
    ))
    runtime = sandbox_result.sequence_runtime_result

    # --- Step 3: Optional YOLO perception ---
    print("[3/6] Running perception...")
    perception_record_path = None
    fused_decision = "approve"
    fused_risk_level = "low"
    rejected = runtime.rejected_steps
    manual_review = runtime.manual_review_steps

    if rejected > 0:
        fused_decision, fused_risk_level = "reject", "high"
    elif manual_review > 0:
        fused_decision, fused_risk_level = "manual_review", "medium"

    if not args.skip_yolo and args.yolo_model and args.image:
        from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter  # noqa: PLC0415
        from perception.adapters.base import PerceptionInferenceRequest  # noqa: PLC0415
        from perception.inference_runner import run_perception_inference  # noqa: PLC0415
        from perception.inference_record import write_perception_inference_record  # noqa: PLC0415

        adapter = UltralyticsYoloAdapter(
            args.yolo_model,
            default_zone_by_class={"person": "danger_zone"},
        )
        request = PerceptionInferenceRequest(
            input_path=Path(args.image), sequence_id=seq.sequence_id, frame_id="frame_000001",
        )
        record = run_perception_inference(
            adapter=adapter, request=request,
            original_decision=fused_decision, original_risk_level=fused_risk_level,
            adapter_kind="ultralytics_yolo",
        )
        perception_record_path = out / "perception_inference_record.json"
        write_perception_inference_record(record, perception_record_path)
        fused_decision = record.fusion_result.get("fused_decision", fused_decision)
        fused_risk_level = record.fusion_result.get("fused_risk_level", fused_risk_level)
        print(f"  -> Fused: {fused_decision} ({fused_risk_level})")
    else:
        print(f"  -> Original: {fused_decision} ({fused_risk_level})")

    # --- Step 4: Write external trajectory record and diagnostic context ---
    print("[4/6] Writing evidence...")
    ext_rec = ExternalTrajectoryRecord(
        dataset_name=traj.dataset_name, episode_id=traj.episode_id,
        robot_name=traj.robot_name, action_type=traj.action_type,
        frame_count=len(traj.frames), mapping=mapping_data,
        source_path=str(Path(args.episode).resolve()), sequence_id=seq.sequence_id,
    )
    rec_path = out / "external_trajectory_record.json"
    write_external_trajectory_record(ext_rec, rec_path)

    ctx = out / "diagnostic_context.json"
    ctx.write_text(json.dumps({
        "episode_id": runtime.episode_dir.name, "total_steps": runtime.total_steps,
        "approved_steps": runtime.approved_steps, "rejected_steps": runtime.rejected_steps,
        "manual_review_steps": runtime.manual_review_steps, "artifacts": [],
    }), encoding="utf-8")

    manifest = build_evidence_manifest(
        context_path=ctx,
        external_trajectory_record_path=rec_path,
        perception_record_path=perception_record_path,
    )
    manifest_path = out / "evidence_manifest.json"
    write_evidence_manifest(manifest, manifest_path)
    print(f"  -> evidence groups: {[k for k, v in manifest.get('evidence_groups', {}).items() if v.get('available')]}")

    # --- Step 5: Optional LLM final answer ---
    print("[5/6] Generating LLM advisory answer...")
    if not args.skip_llm and args.llm_provider == "fake":
        answer = generate_fake_final_answer(
            fused_decision=fused_decision, fused_risk_level=fused_risk_level,
            dataset_name=traj.dataset_name,
        )
    elif not args.skip_llm and args.llm_provider in ("deepseek", "openai"):
        # Real LLM provider path — uses the existing diagnostic analysis pipeline
        from diagnostics.analysis.fake_analyst import run_fake_diagnostic_analyst  # noqa: PLC0415
        context_data = json.loads(ctx.read_text(encoding="utf-8"))
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        analysis = run_fake_diagnostic_analyst(context=context_data, manifest=manifest_data)
        answer = LLMFinalAnswer(
            provider=args.llm_provider, model=args.llm_model or "unknown",
            advisory_decision=analysis.deterministic_outcome.get("final_status", "unknown"),
            risk_level=analysis.deterministic_outcome.get("fused_risk_level", fused_risk_level),
            short_answer=analysis.risk_summary,
            reasoning_summary=analysis.risk_summary,
            evidence_refs=tuple(analysis.evidence_used),
        )
    else:
        answer = None

    if answer is not None:
        llm_path = out / "llm_diagnostic_analysis.json"
        write_final_answer(answer, llm_path)
        print(f"  -> Advisory: {answer.advisory_decision}")

    # --- Step 6: Write final_answer.md and summary.md ---
    print("[6/6] Writing final output...")
    llm_line = f"- LLM Advisory: {answer.advisory_decision} ({answer.risk_level})" if answer else "- LLM: skipped"
    evidence_line = f"- External Trajectory Evidence: {manifest['checks']['has_external_trajectory_evidence']}"

    final_md = f"""# Final Safety Diagnostic Answer

## Deterministic Safety Result
- Original decision: approve
- Fused decision: {fused_decision}
- Risk level: {fused_risk_level}
- Approved steps: {runtime.approved_steps}
- Rejected steps: {runtime.rejected_steps}
- Manual review steps: {runtime.manual_review_steps}

## LLM Advisory Answer
{llm_line}

## Evidence
{evidence_line}
- External trajectory record valid: {manifest['checks']['external_trajectory_record_valid']}
- Evidence groups: {[k for k, v in manifest.get('evidence_groups', {}).items() if v.get('available')]}

## Boundary
LLM advisory output is not used to execute robot actions.
Safety decisions are made by the deterministic SafetyRuntime.
"""
    final_path = out / "final_answer.md"
    final_path.write_text(final_md, encoding="utf-8")

    summary_md = f"""# Integrated Demo Summary
- Trajectory: {traj.dataset_name} / {traj.episode_id}
- Frames: {len(traj.frames)} → Steps: {runtime.total_steps}
- Fused: {fused_decision} ({fused_risk_level})
- Perception: {'YOLO' if perception_record_path else 'none'}
- LLM: {answer.provider if answer else 'none'}
- Manifest: {manifest_path.name}
"""
    summary_path = out / "summary.md"
    summary_path.write_text(summary_md, encoding="utf-8")

    print(f"\nDone. Output in: {out}")
    print(f"  final_answer.md — deterministic + advisory result")


if __name__ == "__main__":
    main()
