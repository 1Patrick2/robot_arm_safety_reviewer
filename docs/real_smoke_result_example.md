# Real Perception Smoke Result Example

This document records a successful real smoke run using YOLO ONNX on a single image.

## Environment

- **OS:** Windows 11 23H2
- **Python:** 3.13.13
- **Ultralytics:** 8.4.75
- **ONNX Runtime:** 1.27.0 (CPUExecutionProvider)
- **Model:** YOLO26n (exported to ONNX opset 20)
- **Test image:** Ultralytics `bus.jpg` (640×480, 137 KB)

## Run Command

```powershell
python tools/run_real_perception_smoke.py ^
  --model local_data/real_perception_smoke/yolo26n.onnx ^
  --image local_data/real_perception_smoke/bus.jpg ^
  --out artifacts/real_perception_smoke_onnx ^
  --person-zone danger_zone
```

## Detection Results

| Class | Count |
|---|---|
| person | 4 |
| bus | 1 |

## Fusion Output

| Field | Value |
|---|---|
| Original Decision | approve |
| Fused Decision | **reject** |
| Fused Risk Level | **high** |
| Triggered Observations | 4 (human_in_danger_zone) |
| Inference Latency | 22.1 ms (pure inference, no model load) |

## Generated Artifacts

| File | Contents |
|---|---|
| `perception_inference_record.json` | Full record (latency, detections, observations, fusion) |
| `evidence_manifest.json` | Evidence manifest with `perception` group available |
| `summary.md` | Human-readable summary |

## Evidence Manifest Perception Group

```json
{
  "checks": {
    "has_perception_evidence": true,
    "perception_record_valid": true
  },
  "evidence_groups": {
    "perception": {
      "available": true,
      "summary_fields": [
        "perception_adapter",
        "perception_observation_count",
        "perception_triggered_observation_count",
        "perception_fused_decision",
        "perception_fused_risk_level"
      ]
    }
  }
}
```

## Key Takeaway

The real YOLO model detected persons in the image, which were mapped to `danger_zone` via `default_zone_by_class`. Each detection produced `human_in_danger_zone` SafetyObservations, which caused `fuse_safety_with_perception()` to escalate the original `approve` decision to `reject` (risk `high`). The full chain — from model inference through evidence manifest — ran successfully.
