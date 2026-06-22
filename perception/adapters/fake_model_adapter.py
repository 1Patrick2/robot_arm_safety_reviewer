from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from perception.models import PerceptionDetection, PerceptionFrame, PerceptionResult

from .base import PerceptionInferenceRequest


class FakePerceptionModelAdapter:
    """Deterministic fake perception model adapter for testing.

    Does not read real images, does not depend on ONNX, OpenCV, Torch,
    or any real model runtime. Can be initialised with predefined
    detections or a predefined ``PerceptionResult``.

    This adapter must not expose ``approve``, ``reject``, ``manual_review``,
    ``send_action``, ``execute``, or ``step`` methods.
    """

    def __init__(
        self,
        detections: tuple[PerceptionDetection, ...] | None = None,
        result: PerceptionResult | None = None,
    ) -> None:
        self._detections = detections
        self._result = result

    def infer(self, request: PerceptionInferenceRequest) -> PerceptionResult:
        """Return a predetermined ``PerceptionResult`` based on construction params.

        Args:
            request: The inference request (sequence_id and frame_id are used).

        Returns:
            A ``PerceptionResult`` conforming to ``perception_result.v1``.
        """
        if self._result is not None:
            if request.sequence_id is not None:
                return replace(self._result, sequence_id=request.sequence_id)
            return self._result

        detections = self._detections or ()
        return PerceptionResult(
            schema_version="perception_result.v1",
            sequence_id=request.sequence_id,
            frames=(
                PerceptionFrame(
                    frame_id=request.frame_id,
                    detections=detections,
                ),
            ),
        )
