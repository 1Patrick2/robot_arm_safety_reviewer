# Robot Action Safety Sandbox Main Prompt

Use this file as the project handoff prompt for new sessions.

## Project Identity

Project name: Robot Action Safety Sandbox.

Current positioning: robot action safety evaluation + diagnostic evidence framework.

This is not a generic Agent project. Optional LLM diagnostic analysis is an evidence explanation layer only.

Safety decisions are made by deterministic runtime logic, not by an LLM or agent.

## Current Stage

**v0.2 complete** — External trajectory pipeline, real LLM advisory, real integrated demo, test consolidation.

Branch `feature/external-trajectory-adapter` ready for merge to `master` and `v0.2` tag.

## Top-Level Layout

```
robot/          Robot domain (safety, runtime, backends, adapters)
perception/     Perception schema, model adapters, fusion, inference evidence
diagnostics/    Context, evidence, contracts, analysis, report, storage, geometry
application/    Orchestration services and gateway helpers
cli/            Official CLI
bench/          Scenarios, sample data, smoke templates, benchmark adapters
tools/          Manual operational tools (real smoke runner, integrated demo)
docs/           Architecture docs and validation records
tests/          Capability-level tests and manual smoke tests
```

## Migration Summary (all completed)

- **Robot domain**: `robot_safety/`, `robot_runtime/`, `robots/` → `robot/safety/`, `robot/runtime/`, `robot/backends/`, `robot/adapters/`. Legacy dirs removed.
- **Diagnostics**: `diagnostic_runtime/` → `diagnostics/` (context, tools, report, runtime, agent, guardrails, analysis). `reports/evidence_manifest` → `diagnostics/evidence/`. `sim/` geometry → `diagnostics/geometry/`. `runtime_db/` → `diagnostics/storage/`.
- **Top-level layout**: `gateway/` → `application/gateway/`. `reports/` → `diagnostics/report/`. `dataset_adapters/` → `bench/adapters/`. `samples/` → `bench/samples/`. `assets/` → `bench/assets/`. `scripts/` → `tools/`. `sim/` removed.
- **No legacy compatibility shims remain.** All code uses canonical paths.
- **Tests**: from ~60 stage-based (`test_stage*.py`) to 8 capability-level tests + supporting tests. All legacy stage tests removed.

## Completed Capabilities

- SafetyRuntime, PolicyActionSequence, mock/PyBullet backend
- Runtime metrics DB, diagnostic context, deterministic report
- evidence_manifest with evidence_groups, expected_contract
- Diagnostic regression, Level-2 safety scenarios, case-set CLI
- Diagnostic analysis (fake analyst, analysis service, CLI)
- perception_result.v1 schema, loader, fake adapter
- Perception safety fusion rules (`PerceptionSafetyFusionResult`)
- Perception-aware regression fixtures
- Perception model adapter protocol (`PerceptionInferenceRequest`, `PerceptionModelAdapter` Protocol, `FakePerceptionModelAdapter`)
- Perception inference evidence bridge (`PerceptionInferenceRecord`, `run_perception_inference`, manifest perception group)
- Optional real YOLO / ONNX smoke loop (`UltralyticsYoloAdapter`, contract tests, manual smoke)
- Real smoke verified: YOLO26n ONNX, 4 persons + 1 bus, approve → reject, 22.1 ms
- **External trajectory pipeline** (v0.2): LeRobot-style episode schema, ActionMappingConfig, conversion, evidence record
- **Real LLM advisory** (v0.2): call_llm_diagnostic_analysis() for DeepSeek / OpenAI / OpenAI-compatible providers
- **Real integrated demo** (v0.2): tools/run_real_integrated_demo.py — end-to-end pipeline
- **Test consolidation** (v0.2): 8 capability-level tests replace ~60 stage tests

## Reference Documents

- `docs/project_current_status.md` — complete status and scope
- `docs/final_validation.md` — test commands, real smoke result, merge checklist
- `docs/testing_strategy.md` — test structure (capability-level vs manual)
- `docs/real_smoke_result_example.md` — detailed real smoke run record
- `docs/stage54b_perception_inference_evidence.md` — evidence bridge design
- `docs/stage54c_real_yolo_smoke.md` — real YOLO smoke usage
- `docs/real_integrated_demo.md` — integrated demo usage

## Hard Boundaries

- LLM must not approve/reject/manual_review/modify/execute robot actions.
- Safety decisions are made by deterministic `SafetyRuntime`.
- The project is not a motion planner, not a generic Agent framework.
- Real camera, RKNN, and edge deployment are out of scope.
- ONNX Runtime is optional (used only through real smoke, not a hard dependency).
- Perception model adapter produces `PerceptionResult` only — safety decisions remain in fusion layer.
- Real LLM advisory is manual-only and requires API keys (no CI dependency).

## Operating Rules

- New code must use `robot.*`, `perception.*`, `diagnostics.*` canonical paths.
- No new feature expansion in this branch. Current focus: merge, tag, document.
- This project is a safety evaluation + perception fusion framework, not an Agent project.
