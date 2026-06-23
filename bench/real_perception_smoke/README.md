# Real Perception Smoke Data

This folder is for local real-model smoke data.

**Do not commit model weights or images to this repository.**

## Usage

1. Install optional dependencies:
   ```powershell
   python -m pip install ultralytics onnxruntime
   ```

2. Prepare a model (`.pt` or `.onnx`):
   ```powershell
   python -c "from ultralytics import YOLO; YOLO('yolo26n.pt').export(format='onnx')"
   ```

3. Prepare an image (e.g. `bus.jpg` from Ultralytics assets).

4. Run the smoke script:
   ```powershell
   python tools/run_real_perception_smoke.py ^
     --model bench/real_perception_smoke/yolo26n.onnx ^
     --image bench/real_perception_smoke/bus.jpg ^
     --out artifacts/real_perception_smoke ^
     --person-zone danger_zone
   ```

5. Inspect outputs in `artifacts/real_perception_smoke/`.
