"""Run a real YOLO perception smoke loop.

Produces:
    - perception_inference_record.json
    - evidence_manifest.json
    - summary.md

Requires: pip install ultralytics
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a real YOLO perception smoke loop")
    parser.add_argument("--model", required=True, help="Path to .pt or .onnx model")
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--original-decision", default="approve")
    parser.add_argument("--original-risk-level", default="low")
    parser.add_argument("--person-zone", default="danger_zone")
    parser.add_argument("--confidence", type=float, default=0.25)
    parser.add_argument("--sequence-id", default="real_yolo_smoke")
    parser.add_argument("--frame-id", default="frame_000001")
    args = parser.parse_args()

    # Lazy imports for optional dependency
    try:
        from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter  # noqa: PLC0415
        from perception.adapters.base import PerceptionInferenceRequest  # noqa: PLC0415
        from perception.inference_runner import run_perception_inference  # noqa: PLC0415
        from perception.inference_record import write_perception_inference_record  # noqa: PLC0415
        from diagnostics.evidence.manifest import build_evidence_manifest, write_evidence_manifest  # noqa: PLC0415
    except ImportError as exc:
        print(f"Missing dependency: {exc}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build adapter
    adapter = UltralyticsYoloAdapter(
        args.model,
        confidence_threshold=args.confidence,
        default_zone_by_class={"person": args.person_zone},
    )

    # Build request
    request = PerceptionInferenceRequest(
        input_path=Path(args.image),
        sequence_id=args.sequence_id,
        frame_id=args.frame_id,
    )

    # Run full inference
    print(f"Running inference on {args.image} with model {args.model} ...")
    record = run_perception_inference(
        adapter=adapter,
        request=request,
        original_decision=args.original_decision,
        original_risk_level=args.original_risk_level,
        adapter_kind="ultralytics_yolo",
    )

    # Write record
    rec_path = out_dir / "perception_inference_record.json"
    write_perception_inference_record(record, rec_path)
    print(f"Written: {rec_path}")

    # Build and write manifest
    ctx = out_dir / "diagnostic_context.json"
    ctx.write_text(json.dumps({"episode_id": args.sequence_id, "artifacts": []}), encoding="utf-8")

    manifest = build_evidence_manifest(
        context_path=ctx,
        perception_record_path=rec_path,
    )
    manifest_path = out_dir / "evidence_manifest.json"
    write_evidence_manifest(manifest, manifest_path)
    print(f"Written: {manifest_path}")

    # Summary
    fusion = record.fusion_result
    obs_count = len(record.safety_observations)
    summary_lines = [
        f"# Real Perception Smoke Summary",
        f"",
        f"- Model: {args.model}",
        f"- Image: {args.image}",
        f"- Detections: {len(record.perception_result.get('frames', [{}])[0].get('detections', []))}",
        f"- Safety Observations: {obs_count}",
        f"- Latency: {record.latency_ms:.1f} ms",
        f"- Original Decision: {fusion.get('original_decision', '?')}",
        f"- Fused Decision: {fusion.get('fused_decision', '?')}",
        f"- Fused Risk Level: {fusion.get('fused_risk_level', '?')}",
        f"- Triggered Observations: {len(fusion.get('triggered_observations', []))}",
    ]
    summary_path = out_dir / "summary.md"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Written: {summary_path}")

    # Terminal output
    print(f"\n=== Results ===")
    print(f"  Fused decision: {fusion.get('fused_decision', '?')} (risk: {fusion.get('fused_risk_level', '?')})")
    print(f"  Latency: {record.latency_ms:.1f} ms")
    print(f"  Observations: {obs_count}")
    print(f"  Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
