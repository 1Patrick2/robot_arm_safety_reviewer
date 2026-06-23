# Project Current Status

## Current Status

- **v0.2 complete** — External trajectory pipeline, real LLM advisory, real integrated demo, test consolidation.
- Branch `feature/external-trajectory-adapter` ready for merge to `master` and `v0.2` tag.

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

## Completed Scope

- **Deterministic Safety Runtime**: joint-space safety gate, benchmark/scorer/replay, mock/PyBullet backends, URDF calibration.
- **Policy Action Pipeline**: PolicyActionSequence, SafetyRuntime multi-step execution, visual sandbox artifacts, runtime metrics DB, agent context.
- **Evidence & Diagnostics**: evidence_manifest.json (runtime, safety, geometry, visual, diagnostic, agent, perception, external_trajectory groups), expected_contract.v1, diagnostic regression, fake LLM analyst.
- **Perception Fusion**: perception_result.v1 schema, model adapter protocol, FakePerceptionModelAdapter, perception safety fusion, inference evidence bridge.
- **Real YOLO/ONNX Perception**: UltralyticsYoloAdapter with lazy import, ONNX support, manual smoke.
- **v0.1 Top-Level Consolidation**: 16 → 9 top-level dirs. Legacy packages removed. Canonical robot.*, perception.*, diagnostics.* paths.
- **v0.2 External Trajectory**: LeRobot-style episode schema, ActionMappingConfig, external_trajectory_to_policy_sequence(), trajectory evidence record.
- **v0.2 Real LLM Advisory**: call_llm_diagnostic_analysis() for DeepSeek, OpenAI, OpenAI-compatible. Returns LLMFinalAnswer.
- **v0.2 Real Integrated Demo**: tools/run_real_integrated_demo.py - external trajectory → SafetyRuntime → optional perception → evidence → optional LLM → final_answer.md.
- **v0.2 Test Consolidation**: ~60 stage test files removed, 8 capability-level tests + supporting tests in place.

## Test Structure

**Capability-level tests** (tests/ root):
- test_safety_pipeline.py — sandbox, collision geometry, kinematics, decision logic
- test_diagnostics_evidence_pipeline.py — manifest, contract, evidence groups
- test_diagnostics_contracts.py — expected contract load/validate/build
- test_diagnostics_analysis.py — analysis models, evidence refs, fake analyst
- test_perception_pipeline.py — schema, adapter, fusion, inference evidence
- test_external_trajectory_pipeline.py — schema, loader, conversion, evidence
- test_integrated_demo_pipeline.py — fake integrated demo artifact chain
- test_import_boundaries.py — import isolation, no legacy paths, no stage tests

**Manual-only tests** (tests/manual/):
- Requires API keys, model weights, or network (not run in CI)

## Current Operating Standard

```powershell
python -m pytest tests -q --ignore=tests/manual
```

Latest: 152 passed, 2 skipped (pybullet optional dep).

## Real YOLO Smoke Result

- Model: YOLO26n ONNX on `bus.jpg`
- Detections: 4 persons, 1 bus
- Original decision: approve → Fused: **reject (high)**
- ONNX inference latency: 22.1 ms

## Known Boundaries

- The project is a safety reviewer, not a planner.
- LLM / diagnostic analysis is evidence-only — it does not approve, reject, or execute robot actions.
- Safety decisions are made by deterministic runtime.
- PyBullet backend and mock backend are diagnostic simulation tools.
- Real camera, RKNN, ONNX runtime as hard dependency, and edge deployment remain out of scope.
- Real LLM advisory is manual-only and requires API keys (no CI dependency).
- CI workflow is configured at .github/workflows/core-tests.yml; check GitHub Actions for latest run status.
