# v0.2 Final Validation

## Core Test Commands

```powershell
# Run all non-manual tests
python -m pytest tests -q --ignore=tests/manual
```

Current result: **152 passed, 2 skipped** (pybullet optional dependency).

## Capability-Level Tests

```powershell
python -m pytest tests/test_safety_pipeline.py tests/test_diagnostics_evidence_pipeline.py tests/test_perception_pipeline.py tests/test_external_trajectory_pipeline.py tests/test_integrated_demo_pipeline.py tests/test_import_boundaries.py tests/test_diagnostics_contracts.py tests/test_diagnostics_analysis.py -q
```

## Fake Integrated Demo

```powershell
python tools/run_real_integrated_demo.py --episode bench/external_trajectory_smoke/lerobot_style_episode.json --mapping bench/external_trajectory_smoke/mapping_config.json --scene bench/external_trajectory_smoke/scene.json --llm-provider fake --out artifacts/real_integrated_demo_fake
```

Expected outputs:
- `final_answer.md`
- `evidence_manifest.json`
- `llm_diagnostic_analysis.json`
- `summary.md`

## Manual Real LLM Smoke

```powershell
$env:RUN_REAL_LLM_SMOKE="1"
$env:LLM_PROVIDER="deepseek"
$env:DEEPSEEK_API_KEY="<your-key>"

python -m pytest tests/manual/test_real_llm_diagnostic_smoke.py -q
```

OpenAI-compatible:
```powershell
$env:RUN_REAL_LLM_SMOKE="1"
$env:LLM_PROVIDER="openai"
$env:OPENAI_API_KEY="<your-key>"

python -m pytest tests/manual/test_real_llm_diagnostic_smoke.py -q
```

## Real YOLO + Real LLM Demo

```powershell
$env:DEEPSEEK_API_KEY="<your-key>"

python tools/run_real_integrated_demo.py ^
  --episode bench/external_trajectory_smoke/lerobot_style_episode.json ^
  --mapping bench/external_trajectory_smoke/mapping_config.json ^
  --scene bench/external_trajectory_smoke/scene.json ^
  --yolo-model local_data/real_perception_smoke/yolo26n.onnx ^
  --image local_data/real_perception_smoke/bus.jpg ^
  --llm-provider deepseek ^
  --out artifacts/real_integrated_demo_real_llm
```

## Recorded Real Perception Smoke Result

- Model: YOLO26n exported to ONNX (opset 20)
- Image: Ultralytics `bus.jpg`
- Detections: 4 persons, 1 bus
- Zone mapping: `{"person": "danger_zone"}`
- Fused decision: **reject** (risk: high)
- ONNX inference latency: 22.1 ms

## GitHub Actions CI

CI workflow is configured at `.github/workflows/core-tests.yml`.

Runs on push/pull_request to `master`. Lightweight: no API keys, no model weights, no network.

Check latest run status at: **Actions → Core Tests** on GitHub.

## v0.2 Merge Checklist

- [x] External trajectory pipeline complete
- [x] Real LLM client (DeepSeek + OpenAI compatible)
- [x] Real integrated demo runner
- [x] Test consolidation: ~60 stage files removed, 8 capability tests in place
- [x] `test_no_stage_named_tests_remain` passes (no test_stage*.py remains)
- [x] Manual real LLM smoke test with proper skip behavior
- [x] .gitignore includes .env
- [x] All non-manual tests pass (152 passed, 2 skipped)
- [x] Fake integrated demo produces all artifacts
- [ ] GitHub Actions Core Tests green (check on GitHub)
- [ ] Merge `feature/external-trajectory-adapter` → `master`
- [ ] Tag `v0.2`
