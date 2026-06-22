from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any

from perception.adapters.base import PerceptionInferenceRequest, PerceptionModelAdapter
from perception.fake_adapter import build_safety_observations
from perception.fusion import fuse_safety_with_perception
from perception.inference_record import PerceptionInferenceRecord


def run_perception_inference(
    *,
    adapter: PerceptionModelAdapter,
    request: PerceptionInferenceRequest,
    original_decision: str,
    original_risk_level: str | None = None,
    adapter_name: str | None = None,
    adapter_kind: str = "fake",
    metadata: dict[str, Any] | None = None,
) -> PerceptionInferenceRecord:
    """Run a full perception inference cycle through the evidence pipeline.

    Measures latency, calls the adapter, builds safety observations,
    fuses with the original deterministic decision, and returns a
    structured ``PerceptionInferenceRecord``.

    Args:
        adapter: A ``PerceptionModelAdapter`` instance.
        request: The inference request (input path, identifiers).
        original_decision: The original deterministic safety decision
            (``"approve"``, ``"manual_review"``, or ``"reject"``).
        original_risk_level: Optional original risk level.
        adapter_name: Display name (defaults to class name).
        adapter_kind: ``"fake"`` (default) or future provider name.
        metadata: Additional context to store in the record.

    Returns:
        A ``PerceptionInferenceRecord`` with all timing, detection,
        observation, and fusion data.

    Strict boundary:
        - Does **not** call ``SafetyRuntime``.
        - Does **not** call ``RobotDeviceAdapter``.
        - Does **not** call ``send_action``.
        - Safety escalation happens only through ``fuse_safety_with_perception()``.
    """
    if adapter_name is None:
        adapter_name = adapter.__class__.__name__

    # Run inference
    t0 = time.perf_counter()
    perception_result = adapter.infer(request)
    t1 = time.perf_counter()
    latency_ms = (t1 - t0) * 1000.0

    # Build safety observations
    observations = build_safety_observations(perception_result)

    # Fuse with deterministic decision
    fusion = fuse_safety_with_perception(
        original_decision=original_decision,
        original_risk_level=original_risk_level,
        observations=observations,
    )

    return PerceptionInferenceRecord(
        adapter_name=adapter_name,
        adapter_kind=adapter_kind,
        input_path=str(request.input_path),
        input_exists=request.input_path.exists(),
        sequence_id=request.sequence_id,
        frame_id=request.frame_id,
        latency_ms=latency_ms,
        perception_result=asdict(perception_result),
        safety_observations=tuple(
            {
                "kind": o.kind,
                "object_id": o.object_id,
                "severity": o.severity,
                "frame_id": o.frame_id,
                "evidence_refs": list(o.evidence_refs),
            }
            for o in observations
        ),
        fusion_result=fusion.to_dict(),
        metadata=metadata or {},
    )
