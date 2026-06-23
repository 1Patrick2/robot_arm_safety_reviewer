# Project Current Status

## Current Status

- **Stage 5.4-B2 Real YOLO / ONNX Perception Smoke Loop — complete.**
- **v0.1 portfolio-ready.** Final hygiene, validation, and merge preparation in progress.
- No further feature expansion in this branch.

## Top-Level Layout

```
robot/          Robot domain (safety, runtime, backends, adapters)
perception/     Perception schema, model adapters, fusion, inference evidence
diagnostics/    Context, evidence, contracts, analysis, report, storage, geometry
application/    Orchestration services and gateway helpers
cli/            Official CLI
bench/          Scenarios, sample data, smoke templates, benchmark adapters
tools/          Manual operational tools (real smoke runner)
docs/           Architecture docs and validation records
tests/          Automated and manual tests
```

## Completed Scope

- Stage 1: deterministic safety gate for joint-space commands.
- Stage 1.5: benchmark, scorer, replay, and report loop.
- Stage 2: backend abstraction, PyBullet diagnostics, mock-vs-PyBullet comparison, and URDF calibration diagnostics.
- Stage 3.1–3.7: application service layer, runtime, dataset adapters, visual sandbox, metrics DB, agent context.
- Stage 3.8A–3.12: evidence hardening, diagnostic tools, report, agent runner, DeepSeek adapter, integration, manifest, regression, documentation.
- Stage 4.2A–4.2D: Level-2 scenarios, expected contracts, case-set CLI, documentation.
- Stage 4.3A–4.3D: evidence groups, required evidence groups, stronger contract checks, docs sync.
- Stage 4.4A–4.4B: diagnostic analysis schema, fake analyst, analysis service CLI.
- Stage 5.1: perception result schema, loader, fake adapter.
- Stage 5.1-polish: unknown safe zone, distance threshold cleanup.
- Stage 5.2: perception safety fusion (`PerceptionSafetyFusionResult`).
- Stage 5.2-polish: fusion edge-case coverage.
- Stage 5.3A: perception-aware regression fixtures and focused tests.
- Stage 5.4A: perception model adapter protocol (`PerceptionInferenceRequest`, `PerceptionModelAdapter` Protocol, `FakePerceptionModelAdapter`).
- Stage 5.4B: perception inference evidence bridge (`PerceptionInferenceRecord`, `run_perception_inference`, manifest perception group).
- Stage 5.4C: optional real YOLO / ONNX smoke loop (`UltralyticsYoloAdapter`, contract tests, manual smoke).
- R1-B1–R1-B6: robot domain migration (`robot_safety/`, `robot_runtime/`, `robots/` → `robot/safety/`, `robot/runtime/`, `robot/backends/`, `robot/adapters/`).
- R1-C: diagnostics package migration (`diagnostic_runtime/` → `diagnostics/`, `reports/evidence` → `diagnostics/evidence/`, `sim/` geometry → `diagnostics/geometry/`).
- v0.1 top-level consolidation: `gateway/` → `application/gateway/`, `runtime_db/` → `diagnostics/storage/`, `reports/` → `diagnostics/report/`, `dataset_adapters/` → `bench/adapters/`, `samples/` → `bench/samples/`, `assets/` → `bench/assets/`, `scripts/` → `tools/`, `sim/` deleted.

## Current Task

- v0.1 final hygiene: stale docs cleanup, obsolete test review, final validation, merge preparation.

## Current Operating Standard

```powershell
python -m pytest tests/test_stage51_perception_schema.py tests/test_stage52_perception_fusion.py tests/test_stage53_perception_regression_cases.py tests/test_stage54_perception_model_adapter.py tests/test_stage54b_perception_inference_evidence.py tests/test_stage54c_ultralytics_yolo_adapter_contract.py tests/test_evidence_manifest.py tests/test_stage42_diagnostic_contracts.py tests/test_stage42_level2_scenarios.py tests/test_diagnostic_cli.py tests/test_r1_robot_canonical_imports.py -q
```

## Latest Focused Validation

```text
157 passed across: perception, adapter, evidence, manifest, contract, CLI, gateway, storage, dataset
```

## Real YOLO Smoke Result

- Model: YOLO26n ONNX on `bus.jpg`
- Detections: 4 persons, 1 bus
- Original decision: approve → Fused: **reject (high)**
- ONNX inference latency: 22.1 ms
- Full evidence manifest with perception group available

## Known Boundaries

- The project is a safety reviewer, not a planner.
- LLM / diagnostic analysis is evidence-only — it does not approve, reject, or execute robot actions.
- Safety decisions are made by deterministic runtime.
- PyBullet backend and mock backend are diagnostic simulation tools.
- Real camera, RKNN, ONNX runtime as hard dependency, and edge deployment remain out of scope.
- `sim/` has been removed; all code migrated to `robot/backends/` and `diagnostics/geometry/`.
