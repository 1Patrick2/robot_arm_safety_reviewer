# v0.1 Final Validation

## Core Pytest Commands

```powershell
# Perception + adapter + evidence + manifest + contract
python -m pytest tests/test_stage51_perception_schema.py tests/test_stage52_perception_fusion.py tests/test_stage53_perception_regression_cases.py tests/test_stage54_perception_model_adapter.py tests/test_stage54b_perception_inference_evidence.py tests/test_stage54c_ultralytics_yolo_adapter_contract.py -q

# Evidence manifest + diagnostic contracts
python -m pytest tests/test_evidence_manifest.py tests/test_stage42_diagnostic_contracts.py -q

# Diagnostic CLI + Level-2 regression
python -m pytest tests/test_diagnostic_cli.py tests/test_stage42_level2_scenarios.py -q

# Canonical robot imports
python -m pytest tests/test_r1_robot_canonical_imports.py -q
```

## Full Pytest Command

```powershell
python -m pytest tests/test_stage51_perception_schema.py tests/test_stage52_perception_fusion.py tests/test_stage53_perception_regression_cases.py tests/test_stage54_perception_model_adapter.py tests/test_stage54b_perception_inference_evidence.py tests/test_stage54c_ultralytics_yolo_adapter_contract.py tests/test_evidence_manifest.py tests/test_stage42_diagnostic_contracts.py tests/test_stage42_level2_scenarios.py tests/test_diagnostic_cli.py tests/test_r1_robot_canonical_imports.py tests/test_stage1_gateway.py tests/test_stage36_episode_ingest.py tests/test_stage34_mini_sequence_adapter.py tests/test_stage34_lerobot_style_adapter.py -q
```

## Stale Import Audit

```powershell
rg "from dataset_adapters|from gateway|from runtime_db|from reports|from sim|robot_safety|robot_runtime|from robots" -g "*.py" .
```

Expected: no results (except references to `diagnostic_runtime_trace` artifact kind strings).

## Manual Real YOLO Smoke

```powershell
$env:RUN_REAL_YOLO_SMOKE="1"; $env:REAL_YOLO_MODEL="local_data/real_perception_smoke/yolo26n.onnx"; $env:REAL_YOLO_IMAGE="local_data/real_perception_smoke/bus.jpg"; python -m pytest tests/manual/test_real_yolo_smoke.py -q
```

## Recorded Real Smoke Result

- Model: YOLO26n exported to ONNX (opset 20)
- Image: Ultralytics `bus.jpg`
- Detections: 4 persons, 1 bus
- Zone mapping: `{"person": "danger_zone"}`
- Fused decision: **reject** (risk: high)
- ONNX inference latency: 22.1 ms
- Artifacts: `perception_inference_record.json`, `evidence_manifest.json`, `summary.md`

## Local Cache Cleanup

```powershell
Remove-Item -Recurse -Force .pytest_cache, .pytest_tmp -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
Remove-Item -Recurse -Force artifacts, output_reports -ErrorAction SilentlyContinue
```

Do **not** delete `local_data/` automatically — it may contain your model weights and test images.

## GitHub Actions CI

Not configured. Validation is local-only at this stage.

## v0.1 Merge Checklist

- [x] Stage 5.4-B2 complete
- [x] Real YOLO / ONNX smoke verified
- [x] All perception tests pass
- [x] All diagnostic tests pass
- [x] All dataset/benchmark tests pass
- [x] Top-level layout consolidated (9 dirs)
- [x] Stale imports audit clean
- [x] sim/ removed
- [x] gateway/ → application/gateway/
- [x] runtime_db/ → diagnostics/storage/
- [x] reports/ → diagnostics/report/
- [x] .gitignore clean
- [ ] Merge `feature/diagnostic-cli` → `master`
- [ ] Tag `v0.1`
