# Stage 5.4-B1: Perception Inference Evidence Bridge

## Motivation

Before running a real model, the evidence chain must be able to capture and record
perception inference results. This stage adds a structured inference record, a runner
that orchestrates adapter → observations → fusion, and a `perception` evidence group
in the manifest.

## Data Flow

```
PerceptionModelAdapter + PerceptionInferenceRequest
  → run_perception_inference()
    → adapter.infer()              [measure latency]
    → build_safety_observations()
    → fuse_safety_with_perception()
    → PerceptionInferenceRecord
      → write_perception_inference_record()  → perception_inference_record.json
      → evidence_manifest.json               → perception evidence group
```

## PerceptionInferenceRecord

| Field | Description |
|---|---|
| `adapter_name` | Class name of the adapter used |
| `adapter_kind` | `"fake"` or future provider |
| `input_path` | Path to the input image / source |
| `input_exists` | Whether the input file exists on disk |
| `latency_ms` | Wall-clock inference time in milliseconds |
| `perception_result` | Full `PerceptionResult.to_dict()` output |
| `safety_observations` | List of observation dicts from `build_safety_observations()` |
| `fusion_result` | Full `PerceptionSafetyFusionResult.to_dict()` output |

## Evidence Manifest Perception Group

When a `perception_inference_record.json` is provided to `build_evidence_manifest()`,
the manifest gains:

- **artifact**: `perception_inference_record`
- **checks**: `has_perception_evidence`, `perception_record_valid`
- **summary fields**: `perception_adapter`, `perception_latency_ms`,
  `perception_observation_count`, `perception_triggered_observation_count`,
  `perception_fused_decision`, `perception_fused_risk_level`
- **evidence group**: `perception` with `available=True`

## Expected Contract Integration

Existing contract fields work without changes:
- `required_artifacts: ["perception_inference_record"]`
- `required_evidence_groups: ["perception"]`

## Safety Boundary

- `run_perception_inference()` does **not** call `SafetyRuntime`.
- It does **not** call `RobotDeviceAdapter` or `send_action`.
- Safety escalation happens only through `fuse_safety_with_perception()`.
