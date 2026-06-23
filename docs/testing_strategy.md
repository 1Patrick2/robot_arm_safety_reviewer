# Testing Strategy

## Three-Layer Validation

### Layer 1: Core CI Tests (GitHub Actions, automatic)

Run on every push/pull_request:

| Test File | Covers |
|---|---|
| `test_safety_pipeline.py` | Scene → sandbox → runtime → approve/reject, collision geometry, kinematics, decision logic, backend factory |
| `test_diagnostics_evidence_pipeline.py` | Evidence manifest, expected contract, evidence groups |
| `test_diagnostics_contracts.py` | ExpectedContract load/validate/build, actual summary, contract edge cases |
| `test_diagnostics_analysis.py` | DiagnosticAnalysis models, evidence_refs, fake analyst |
| `test_perception_pipeline.py` | Perception schema, fake adapter, fusion, inference evidence, ultralytics contract |
| `test_external_trajectory_pipeline.py` | ExternalTrajectory, ActionMappingConfig, conversion, evidence, contract |
| `test_integrated_demo_pipeline.py` | Fake full-chain: trajectory → safety → perception → LLM answer |
| `test_import_boundaries.py` | No legacy imports, no hard model deps, LLM not in safety path, no stage-named tests |

All CI tests are **lightweight**: no network, no model weights, no API keys, no GPU.

### Layer 2: Local Manual Smoke

| Command | Dependency |
|---|---|
| `tools/run_real_perception_smoke.py` | `ultralytics` + YOLO model + test image |
| `tools/run_external_trajectory_smoke.py` | None (uses local fixture) |
| `tools/run_real_integrated_demo.py --llm-provider fake` | None |
| `tools/run_real_integrated_demo.py --llm-provider deepseek` | `DEEPSEEK_API_KEY` |
| `tests/manual/test_real_llm_diagnostic_smoke.py` | `DEEPSEEK_API_KEY` or `OPENAI_API_KEY` |
| `tests/manual/test_real_yolo_smoke.py` | `ultralytics` + model + image |
| `tests/manual/test_lerobot_hub_smoke.py` | `lerobot` + network |

### Layer 3: Portfolio Demo

```powershell
python tools/run_real_integrated_demo.py ^
  --episode bench/external_trajectory_smoke/lerobot_style_episode.json ^
  --mapping bench/external_trajectory_smoke/mapping_config.json ^
  --scene bench/external_trajectory_smoke/scene.json ^
  --yolo-model local_data/real_perception_smoke/yolo26n.onnx ^
  --image local_data/real_perception_smoke/bus.jpg ^
  --llm-provider fake ^
  --out artifacts/real_integrated_demo
```

## Why Capability-Based Tests?

Previously the project had ~15 stage-numbered test files (`test_stage51_*`, `test_stage52_*`, etc.).
These were replaced by **6 capability-level tests** organized by function, not by development phase.
This makes it clear what the project actually tests and reduces cognitive overhead.
