# Project Current Status

Robot Action Safety Sandbox is currently working on **Stage 3.12 Demo Flow & Documentation Hardening — complete**.

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
- Stage 3.8A Evidence Correctness Hardening: scene-based robot model, obstacle rendering, structured evidence data export.
- Stage 3.8B Diagnostic Tools: read-only query layer over diagnostic_context.json.
- Stage 3.8C Deterministic Diagnostic Report: LLM-free report generation.
- Stage 3.8D Diagnostic Agent Runner: fake provider + safety boundary checker on agent output.
- Stage 3.8E DeepSeek Adapter (optional): smoke-only provider, not part of deterministic safety path.
- Stage 3.9 Diagnostic Runtime Integration: runtime runner, runtime trace, integration guardrails.
- Stage 3.10 Evidence Manifest: unified diagnostic output evidence index with artifact existence checks.
- Stage 3.11 Diagnostic Regression: batch pipeline sandbox → metrics → diagnostic run → manifest → summary, with artifact completeness validation.
- Stage 3.12 Demo Flow & Documentation: README command chain, architecture layers, output artifact reference.

## Current Focus

- Stage 3 is complete. The diagnostic runtime pipeline is fully integrated: sandbox → metrics DB → diagnostic context → deterministic report → optional agent with guardrails → evidence manifest → regression summary.
- All CLI commands (`diagnostic run`, `diagnostic report`, `diagnostic regression`) are operational and tested.
- Priority: correctness > interpretability > completeness > LLM integration.
- Keep docs synchronized with the codebase.
- Keep generated artifacts out of git.

## Current Verification Snapshot

Latest recorded focused verification on the local `robotarm-pybullet` conda environment:

```text
Stage 3.3 sequence runtime: 7 passed
Stage 3.4 dataset adapters/service/CLI/integration: 28 passed
Stage 3.5 visual sandbox: 24 passed
Stage 3.6 runtime metrics DB: 34 passed
Stage 3.7 agent context: 30 passed
```

Targeted commands:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage33_sequence_runtime.py -q --basetemp .pytest_tmp\stage33

D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage34_mini_sequence_adapter.py tests/test_stage34_lerobot_style_adapter.py tests/test_stage34_dataset_service.py tests/test_stage34_dataset_cli.py tests/test_stage34_dataset_to_sequence_runtime.py -q --basetemp .pytest_tmp\stage34

D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage35_episode_loader.py tests/test_stage35_runtime_episode_report.py tests/test_stage35_runtime_visual_report.py tests/test_stage35_sandbox_service.py tests/test_stage35_sandbox_cli.py tests/test_stage35_sandbox_pybullet_smoke.py -q --basetemp .pytest_tmp\stage35

D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage36_runtime_db_schema.py tests/test_stage36_runtime_db_repository.py tests/test_stage36_episode_ingest.py tests/test_stage36_metrics_service.py tests/test_stage36_metrics_cli.py tests/test_stage36_sandbox_metrics_integration.py -q --basetemp .pytest_tmp\stage36

D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage37_agent_context_models.py tests/test_stage37_agent_context_builder.py tests/test_stage37_agent_context_render.py tests/test_stage37_agent_context_service.py tests/test_stage37_agent_context_cli.py -q --basetemp .pytest_tmp\stage37
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

## Known Boundaries

- The project is a safety reviewer, not a planner.
- It checks a given linear joint-space trajectory; it does not generate obstacle-avoiding paths.
- The mock backend is a deterministic baseline, not a calibrated robot model.
- The PyBullet backend is a diagnostic simulation backend, not certified hardware validation.
- Exact clearance and attribution can differ between mock and PyBullet; this is measured and documented rather than hidden.
- Self-collision, workspace boundary, velocity/acceleration constraints, RealMan SDK execution, ROS2, MoveIt, VLA, and LLM agent control are not implemented.
- `SafetyRuntime.step()` remains a single-step primitive; `run_sequence_runtime` orchestrates multi-step `PolicyActionSequence` rollouts on top of it.
- CLI output is centralized in `cli/output.py`; command modules should not duplicate result formatting.
- Dataset adapters follow a Protocol-based pattern; `MiniSequenceAdapter` and `LeRobotStyleAdapter` are local sample adapters.
- Visual sandbox artifacts are static reports and PNGs generated from episode logs; this is not an interactive simulator or hardware controller.
- Runtime metrics are audit data; they must not change safety decisions.
- Agent context packages are deterministic diagnostic evidence; they must not approve, reject, modify, or execute robot actions.

## Current Operating Standard

A user can run sandbox with metrics DB, inspect the stored episode, and build a deterministic diagnostic context package:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main sandbox run ^
  --sequence samples/policy_sequences/simple_safe_sequence.json ^
  --scene bench/sim_robot_arm/simple_joint_move_001/scene.json ^
  --backend mock ^
  --output-root output_reports/sandbox ^
  --metrics-db output_reports/runtime_metrics/runtime_metrics.db ^
  --json

D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main metrics list-runs ^
  --db output_reports/runtime_metrics/runtime_metrics.db ^
  --json

D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main context build ^
  --db output_reports/runtime_metrics/runtime_metrics.db ^
  --episode-id episode_xxx ^
  --output-dir output_reports/agent_context/episode_xxx ^
  --json
```

Expected context outputs:

- `diagnostic_context.json`
- `diagnostic_context.md`
