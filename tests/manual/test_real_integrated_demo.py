"""Manual real integrated demo smoke test — requires ultralytics, YOLO model, image.

Skipped unless ``RUN_REAL_YOLO_SMOKE`` is set.
"""

import os
from pathlib import Path
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_REAL_YOLO_SMOKE"),
    reason="Set RUN_REAL_YOLO_SMOKE=1 with REAL_YOLO_MODEL and REAL_YOLO_IMAGE",
)


def test_real_integrated_demo(tmp_path):
    """Run the integrated demo with real YOLO + fake LLM."""
    from tools.run_real_integrated_demo import main as demo_main
    import sys

    model = os.environ.get("REAL_YOLO_MODEL")
    image = os.environ.get("REAL_YOLO_IMAGE")
    assert model and image, "REAL_YOLO_MODEL and REAL_YOLO_IMAGE must be set"

    # Build args list
    sys.argv = [
        "run_real_integrated_demo.py",
        "--episode", str(Path(__file__).resolve().parents[2] / "bench" / "external_trajectory_smoke" / "lerobot_style_episode.json"),
        "--mapping", str(Path(__file__).resolve().parents[2] / "bench" / "external_trajectory_smoke" / "mapping_config.json"),
        "--scene", str(Path(__file__).resolve().parents[2] / "bench" / "external_trajectory_smoke" / "scene.json"),
        "--yolo-model", model,
        "--image", image,
        "--llm-provider", "fake",
        "--out", str(tmp_path / "demo_out"),
    ]
    demo_main()

    out = tmp_path / "demo_out"
    assert (out / "final_answer.md").exists()
    assert (out / "evidence_manifest.json").exists()
    assert (out / "llm_diagnostic_analysis.json").exists()
    assert (out / "perception_inference_record.json").exists()
