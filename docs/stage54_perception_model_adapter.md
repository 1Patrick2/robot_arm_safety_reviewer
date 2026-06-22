# Stage 5.4-A: Perception Model Adapter Protocol

## 1. Motivation

Stage 5.1–5.3 built the perception pipeline using hand-crafted `perception_result.json` files.
Stage 5.4-A introduces a formal model-adapter boundary so that real model inference output
can enter the same pipeline — without compromising the deterministic safety boundary.

## 2. Boundary

- **Model adapter is perception-only.**
- It outputs `PerceptionResult` only.
- It must **not** produce `approve` / `reject` / `manual_review`.
- It must **not** call `SafetyRuntime`, `RobotDeviceAdapter`, or any robot execution path.
- It must **not** modify action sequences.
- Deterministic safety fusion remains responsible for safety escalation.

## 3. Data Flow

```
image / mock input
  → PerceptionInferenceRequest
    → PerceptionModelAdapter (Protocol)
      → PerceptionResult (perception_result.v1)
        → load_perception_result() [schema validation]
          → build_safety_observations()
            → SafetyObservation[]
              → fuse_safety_with_perception()
                → PerceptionSafetyFusionResult
```

## 4. Adapter Interface

```python
@dataclass(frozen=True)
class PerceptionInferenceRequest:
    input_path: Path
    sequence_id: str | None = None
    frame_id: str = "frame_000001"
    metadata: dict[str, Any] = field(default_factory=dict)

class PerceptionModelAdapter(Protocol):
    def infer(self, request: PerceptionInferenceRequest) -> PerceptionResult:
        ...
```

The `PerceptionModelAdapter` is a `typing.Protocol` — any object with an
`infer(request) -> PerceptionResult` method satisfies the contract.

## 5. Fake Adapter

`FakePerceptionModelAdapter` is a deterministic implementation for tests:

```python
# With predefined detections:
adapter = FakePerceptionModelAdapter(detections=(PerceptionDetection(...),))

# With a full preset result:
adapter = FakePerceptionModelAdapter(result=predefined_perception_result)
```

It does not:
- Read real images
- Depend on ONNX, OpenCV, Torch, RKNN, or any model runtime

## 6. Safety Invariants

These invariants are enforced by the adapter protocol and must hold for all
future implementations (ONNX, YOLO, RKNN, etc.):

```
- Model output must be PerceptionResult.
- Model output must conform to perception_result.v1 schema.
- Model must not output approve/reject/manual_review.
- Model must not call SafetyRuntime.step().
- Model must not call RobotDeviceAdapter.send_action().
- Fusion layer remains the sole decision-escalation path.
```

## 7. Future Stages

| Stage | Scope |
|---|---|
| Stage 5.4-B | Optional ONNX adapter skeleton (no hard dependency) |
| Stage 5.4-C | YOLO detection postprocess and detection mapping |
| Stage 5.4-D | Model inference evidence summary in manifest |
| Stage 5.5-A | RKNN deployment notes / optional branch |
| Stage 5.5-B | Optional RKNN adapter skeleton |
