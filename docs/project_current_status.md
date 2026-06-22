# Project Current Status

Current functional status:

- Completed through Stage 5.4-A.

Current architecture refactor status:

- R1-B6 completed.
- `robot/` is the only canonical robot-domain package.
- Legacy packages `robot_safety/`, `robot_runtime/`, and `robots/` have been removed.
- `sim/` backend core shims (`base.py`, `backend_factory.py`, `mock_backend.py`, `pybullet_backend.py`) have been removed.
- `sim/` diagnostic geometry modules (`pybullet_diagnostics.py`, `urdf_calibration.py`) are now compatibility shims (moved to `diagnostics/geometry/`).
- `diagnostics/` is now the canonical diagnostics package.
- `reports/evidence_manifest.py` is compatibility-only (implementation at `diagnostics/evidence/manifest.py`).
- New robot-domain implementation code must use `robot.*` imports.

Current task:

- R1-C validation and polish: stabilize the diagnostics migration, update documentation.

Next recommended migration:

- R1-C validation is in progress. Model adapter / ONNX / RKNN work is out of scope until R1-C passes.

Paused:

- Stage 5.3-B perception-aware regression summary integration.

## Completed Scope

- Stage 1 deterministic safety gate.
- Stage 1.5 benchmark, scorer, replay, and report loop.
- Stage 2 PyBullet backend diagnostics.
- Stage 2.6 documentation and evaluator metadata cleanup.
- Stage 3 MVP runtime action loop.
- Stage 3.0 runtime cleanup: execution-result propagation, episode schema hardening, and CLI safety checks.
- Stage 3.1 application service layer, unified CLI entry point, and shared CLI output formatting.
- Stage 3.2 `PolicyAction` and `PolicyActionSequence`.
- Stage 3.3 sequence runtime for multi-step policy action execution.
- Stage 3.4 Dataset Adapter MVP: `MiniSequenceAdapter` and `LeRobotStyleAdapter`.
- Stage 3.5 Visual Runtime Sandbox: episode summary, clearance curve, trajectory overview, sandbox service, and sandbox CLI.
- Stage 3.6 Runtime Metrics DB: SQLite schema, repository, episode ingest, metrics service, metrics CLI, and optional sandbox metrics integration.
- Stage 3.7 Agent Context Runtime: data models, builder from metrics DB, JSON/Markdown renderer, application service, and context build CLI.
- Stage 3.8A-3.8E: evidence correctness hardening, diagnostic tools, deterministic report, agent runner guardrails, DeepSeek adapter.
- Stage 3.9 Diagnostic Runtime Integration: runtime runner, runtime trace, integration guardrails.
- Stage 3.10 Evidence Manifest: unified diagnostic output evidence index with artifact existence checks.
- Stage 3.11 Diagnostic Regression: batch pipeline sandbox → metrics → diagnostic run → manifest → summary, with artifact completeness validation.
- Stage 3.12 Demo Flow & Documentation: README command chain, architecture layers, output artifact reference.
- Stage 4.2A Expected Contract Scaffold: `ExpectedContract` dataclass, `load_expected_contract()`, `build_actual_summary()`, `validate_expected_contract()`.
- Stage 4.2B Level-2 Safety Scenarios: 3 Level-2 cases (`near_threshold_clearance_sequence`, `midpoint_collision_sequence`, `mixed_decision_sequence`) with `expected_contract.json`.
- Stage 4.2C Case-set CLI Integration: `diagnostic regression` supports `--case-set {smoke,level2,all}`.
- Stage 4.3A Evidence Groups: `evidence_manifest.json` includes `evidence_groups` for runtime/safety/geometry/visual/structured_visual/diagnostic/agent.
- Stage 4.3B Evidence Group Contracts: `expected_contract.v1` supports `required_evidence_groups`.
- Stage 4.3C Stronger Expected-vs-Actual Checks: `expected_contract.v1` supports `required_actual_fields`, `expected_closest_obstacle`, `min_clearance_lte`, and `min_clearance_gte`.
- Stage 4.4A Diagnostic Analysis Schema: `DiagnosticAnalysis` / `RootCauseHypothesis` and deterministic fake analyst.
- Stage 4.4A-polish: fake analyst evidence_refs consistency cleanup.
- Stage 4.4B Diagnostic Analysis Service + CLI: `diagnostic analyze` writes `llm_diagnostic_analysis.json`.
- Stage 5.1 Perception Result Schema + Fake Perception Adapter: `perception_result.v1`, loader, and fake adapter.
- Stage 5.1-polish: unknown safe zone and distance threshold cleanup.
- Stage 5.2 Perception Safety Fusion: deterministic fusion rules for perception observations and trajectory results.
- Stage 5.2-polish: focused fusion edge-case coverage.
- Stage 5.3-A Perception-Aware Regression Fixtures: perception-aware scenarios and focused tests.
- Stage 5.4-A Perception Model Adapter Protocol: `PerceptionInferenceRequest`, `PerceptionModelAdapter` Protocol, `FakePerceptionModelAdapter`.
- Stage R1-B1 through R1-B6 Robot Domain Migration: `robot_safety/`, `robot_runtime/`, `robots/` migrated to `robot/safety/`, `robot/runtime/`, `robot/backends/`, `robot/adapters/`. Legacy packages and shims removed after R1-B6. All internal imports now use `robot.*` paths.

## Current Focus

- R1-B6 is completed. Robot domain is now canonical under `robot/`.
- Stage 5.3-B feature work is paused until R1-C diagnostics migration is planned.
- Next planned migration: R1-C diagnostics package migration (`diagnostic_runtime/` → `diagnostics/`).
- Keep generated artifacts out of git.

## Current Operating Standard

Current focused refactor validation:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_r1_robot_safety_package.py -q
```

Perception-focused validation:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_r1_robot_safety_package.py tests/test_stage51_perception_schema.py tests/test_stage52_perception_fusion.py tests/test_stage53_perception_regression_cases.py -q
```

Do not run full pytest repeatedly during R1 polish tasks.

## Latest Focused Validation

```text
38 passed across: test_diagnostic_cli.py, test_stage42_level2_scenarios.py, test_stage42_diagnostic_contracts.py
24 passed across: test_evidence_manifest.py, test_stage36_episode_ingest.py
```

## Evidence Correctness Principles

1. **Images are evidence, not decoration.** Every PNG must be reproducible from structured data.
2. **Robot model must be traceable.** FK chains must either use the scene's robot model or explicitly declare a fallback.
3. **Obstacles must appear in trajectory visuals.** Without obstacle rendering, a clearance value cannot be visually verified.
4. **FK numeric stability must be tested.** All-zero joints, single-joint motions, and multi-joint targets must produce correct FK chains.

## Main Documents

- `README.md`: project entry point and quick start.
- `README.zh-CN.md`: Chinese README.
- `docs/project_architecture.md`: architecture, data flow, layer responsibilities, and boundaries.
- `docs/core_function_map.md`: quick code-reading map.
- `docs/interview_notes.md`: interview and resume narrative.
- `docs/stage2_backend_diagnostics.md`: mock-vs-PyBullet diagnostics and calibration details.
- `docs/stage2_backend_diagnostics.zh-CN.md`: Chinese Stage 2 backend diagnostics.
- `docs/windows_pybullet_setup.md`: Windows PyBullet environment setup.
- `docs/stage4_llm_diagnostic_analysis_plan.md`: Stage 4 design document.

## Known Boundaries

- The project is a safety reviewer, not a planner.
- It checks a given linear joint-space trajectory; it does not generate obstacle-avoiding paths.
- The mock backend is a deterministic baseline, not a calibrated robot model.
- The PyBullet backend is a diagnostic simulation backend, not certified hardware validation.
- Exact clearance and attribution can differ between mock and PyBullet; this is measured and documented rather than hidden.
- Self-collision, workspace boundary, velocity/acceleration constraints, RealMan SDK execution, ROS2, MoveIt, VLA, and LLM agent control are not implemented.
- `SafetyRuntime.step()` remains a single-step primitive.
- Dataset adapters follow a Protocol-based pattern; `MiniSequenceAdapter` and `LeRobotStyleAdapter` are local sample adapters.
- Visual sandbox artifacts are static reports and PNGs generated from episode logs.
- Runtime metrics are audit data; they must not change safety decisions.
- Agent context packages are deterministic diagnostic evidence; they must not approve, reject, modify, or execute robot actions.
- LLM diagnostic analysis is optional and does not affect safety decisions.
- The project does not currently require edge deployment, ONNX, RKNN, or a real camera.
- Stage 5 structured perception input and fusion rules exist, but real camera/model deployment is still out of scope.
- `robot/safety/` is the canonical home for robot safety; legacy `robot_safety/` removed after R1-B6.
