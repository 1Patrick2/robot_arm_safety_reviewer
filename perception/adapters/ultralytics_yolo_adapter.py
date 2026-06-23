from __future__ import annotations

from pathlib import Path
from typing import Any

from perception.models import PerceptionDetection, PerceptionFrame, PerceptionResult
from perception.adapters.base import PerceptionInferenceRequest


class UltralyticsYoloAdapter:
    """Real YOLO model adapter using Ultralytics.

    Supports ``.pt`` and ``.onnx`` model formats.  Lazy-imports ultralytics
    so the rest of the project is not affected when the package is absent.

    This adapter must **not** expose:
        - ``approve`` / ``reject`` / ``manual_review``
        - robot runtime or device adapter calls
        - action execution methods

    It produces ``PerceptionResult`` only — safety decisions remain
    in ``fuse_safety_with_perception()``.
    """

    def __init__(
        self,
        model_path: str | Path,
        *,
        confidence_threshold: float = 0.25,
        class_allowlist: tuple[str, ...] | None = None,
        default_zone_by_class: dict[str, str] | None = None,
    ) -> None:
        self._model_path = str(model_path)
        self._confidence_threshold = confidence_threshold
        self._class_allowlist = class_allowlist
        self._default_zone_by_class = default_zone_by_class or {}
        self._model = None

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from ultralytics import YOLO  # type: ignore[import-untyped]  # noqa: PLC0415
        except ImportError as exc:
            raise RuntimeError(
                "UltralyticsYoloAdapter requires optional dependency 'ultralytics'. "
                "Install with: pip install ultralytics"
            ) from exc
        self._model = YOLO(self._model_path)
        return self._model

    def infer(self, request: PerceptionInferenceRequest) -> PerceptionResult:
        """Run YOLO inference on *request.input_path*.

        Args:
            request: Inference request with the image path.

        Returns:
            A ``PerceptionResult`` with per-frame detections.
        """
        model = self._load_model()
        results = model(str(request.input_path))
        return self._convert_results(request, results)

    def _convert_results(
        self,
        request: PerceptionInferenceRequest,
        results: Any,
    ) -> PerceptionResult:
        """Convert Ultralytics results to a ``PerceptionResult``."""
        detections: list[PerceptionDetection] = []

        for ri, result in enumerate(results):
            if result.boxes is None:
                continue
            names = result.names if hasattr(result, "names") else {}
            boxes_data = result.boxes.data  # shape (N, 6) — xyxy, conf, cls
            # Ensure compatibility across GPU / CPU / different Ultralytics versions
            if hasattr(boxes_data, "cpu"):
                boxes_data = boxes_data.cpu()
            if hasattr(boxes_data, "numpy"):
                boxes_data = boxes_data.numpy()

            for bi in range(boxes_data.shape[0]):
                row = boxes_data[bi]
                x1, y1, x2, y2 = float(row[0]), float(row[1]), float(row[2]), float(row[3])
                conf = float(row[4])
                cls_id = int(row[5])

                if conf < self._confidence_threshold:
                    continue

                class_name = names.get(cls_id, f"class_{cls_id}")

                if self._class_allowlist is not None and class_name not in self._class_allowlist:
                    continue

                zone = self._default_zone_by_class.get(class_name)
                obj_id = f"{class_name}_{ri}_{bi}"

                detections.append(PerceptionDetection(
                    object_id=obj_id,
                    class_name=class_name,
                    confidence=conf,
                    bbox_xyxy=(x1, y1, x2, y2),
                    zone=zone,
                    distance_m=None,
                ))

        return PerceptionResult(
            schema_version="perception_result.v1",
            sequence_id=request.sequence_id,
            frames=(
                PerceptionFrame(
                    frame_id=request.frame_id,
                    detections=tuple(detections),
                ),
            ),
        )
