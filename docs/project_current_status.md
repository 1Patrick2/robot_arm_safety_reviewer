# Project Current Status

Robot Action Safety Sandbox current status: **Stage 4.2-C completed; Stage 4.2-D documentation sync in progress.**

Next stage: **Stage 4.3 evidence groups and expected-vs-actual regression hardening.**

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

## Current Focus

- Stage 4.2 is functionally complete: expected contracts are validated end-to-end across 3 Level-2 scenarios.
- Priority: correctness > interpretability > completeness > LLM integration.
- Keep docs synchronized with the codebase.
- Keep generated artifacts out of git.

## Current Operating Standard

The primary regression command:

```powershell
python -m cli.main diagnostic regression --case-set all --output-dir output_reports/stage42_all --json
```

Regression case sets:

```powershell
python -m cli.main diagnostic regression --case-set smoke --json
python -m cli.main diagnostic regression --case-set level2 --json
python -m cli.main diagnostic regression --case-set all --json
```

Level-2 cases each produce `pipeline_passed`, `evidence_complete`, and `contract_passed` in regression output.

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
