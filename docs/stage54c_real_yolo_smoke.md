# Stage 5.4-B2: Real YOLO / ONNX Perception Smoke Loop

## Why Real Smoke

The project now has a complete model-adapter protocol and evidence bridge.
Running a real model on a real image proves the chain actually works end-to-end.

## Optional Dependency Design

- `UltralyticsYoloAdapter` lazy-imports `ultralytics`. If the package is absent,
  construction succeeds but inference raises a clear `RuntimeError`.
- Contract tests always pass — they never require the optional dependency.
- Manual smoke tests are gated behind `RUN_REAL_YOLO_SMOKE=1`.

## Data Flow

```
image.jpg
  → UltralyticsYoloAdapter.infer()
    → PerceptionResult
      → run_perception_inference()
        → build_safety_observations()
        → fuse_safety_with_perception()
        → PerceptionInferenceRecord
          → write_perception_inference_record()
          → evidence_manifest.json (perception group)
```

## How to Run

### 1. Install optional deps

```powershell
python -m pip install ultralytics onnxruntime
```

### 2. Prepare model

```powershell
python -c "from ultralytics import YOLO; YOLO('yolo26n.pt').export(format='onnx')"
```

### 3. Run smoke script

```powershell
python tools/run_real_perception_smoke.py ^
  --model local_data/real_perception_smoke/yolo26n.onnx ^
  --image local_data/real_perception_smoke/bus.jpg ^
  --out artifacts/real_perception_smoke ^
  --person-zone danger_zone
```

### 4. Run manual test

```powershell
$env:RUN_REAL_YOLO_SMOKE="1"
$env:REAL_YOLO_MODEL="local_data/real_perception_smoke/yolo26n.onnx"
$env:REAL_YOLO_IMAGE="local_data/real_perception_smoke/bus.jpg"
python -m pytest tests/manual/test_real_yolo_smoke.py -q
```

## Safety Boundary

- `UltralyticsYoloAdapter` produces `PerceptionResult` only.
- It does not expose `approve`/`reject`/`manual_review`.
- It does not call `SafetyRuntime` or `RobotDeviceAdapter`.
- Safety escalation happens only through `fuse_safety_with_perception()`.

## Artifacts

| File | Contents |
|---|---|
| `perception_inference_record.json` | Full inference record (latency, detections, fusion) |
| `evidence_manifest.json` | Evidence manifest with perception group |
| `summary.md` | Human-readable summary |

## Future Path

- `ONNXRuntimeAdapter`: pure ONNX Runtime inference without Ultralytics wrapper
- `RKNN adapter`: Rockchip NPU deployment
