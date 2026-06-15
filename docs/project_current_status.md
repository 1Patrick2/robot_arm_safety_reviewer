# Project Current Status

RobotArmSafetyReviewer has completed **Stage 3.6 Runtime Metrics DB**.

This stage adds a structured metrics database (SQLite) for querying episode results alongside the existing visual sandbox artifacts.

## Completed Scope

- Stage 1 deterministic safety gate.
- Stage 1.5 benchmark, scorer, replay, and report loop.
- Stage 2 PyBullet backend diagnostics.
- Stage 2.6 documentation and explicit evaluator metadata cleanup.
- Stage 3 MVP runtime action loop.
- Stage 3.0 runtime cleanup: execution-result propagation, episode schema hardening, and CLI safety checks.
- Stage 3.1 application service layer, unified CLI entry point, shared CLI output formatting.
- Stage 3.2 PolicyAction and PolicyActionSequence models with joint_target / delta_joint conversion.
- Stage 3.3 sequence runtime for multi-step policy action execution with approve / manual_review / reject blocking and episode recording.
- Stage 3.4 Dataset Adapter MVP: DatasetAdapter Protocol, MiniSequenceAdapter (samples/policy_sequences), LeRobotStyleAdapter (samples/lerobot_style), dataset service, dataset CLI, and dataset-backed sequence runtime smoke.
- Stage 3.5 Visual Runtime Sandbox: episode loader, episode summary report, clearance curve artifact, trajectory overview artifact, sandbox service, sandbox CLI, and PyBullet smoke test.
- Stage 3.6 Runtime Metrics DB: SQLite schema, repository, episode ingest, metrics service, metrics CLI, and optional sandbox metrics integration.
- Stage 3.7 Agent Context Runtime: data models, builder from metrics DB, context render (JSON + Markdown), application service, and context build CLI.

## Current Focus

- Stage 3.7 Agent Context Runtime is complete: models, builder, renderer, service, and CLI.
- Stage 3.7 is a deterministic evidence packaging layer — no LLM calls.
- Next: Stage 3.8 Diagnostic-only LLM agent (only after agent context is stable).
- No DeepSeek, RealMan SDK, ROS2 until Stage 3.8 is planned and bounded.

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

## Main Documents

- `README.md`: project entry point and quick start.
- `README.zh-CN.md`: Chinese README.
- `docs/project_architecture.md`: architecture, data flow, layer responsibilities, and boundaries.
- `docs/core_function_map.md`: quick code-reading map.
- `docs/interview_notes.md`: interview and resume narrative.
- `docs/lerobot_interface_study.md`: Stage 3 positioning for a LeRobot-compatible safety runtime.
- `docs/research/agent_project_radar.md`: pattern-first radar for agent and robot-data projects.
- `docs/research/agent_architecture_patterns.md`: adoption patterns that fit this project.
- `docs/research/adoption_decisions.md`: explicit adopt/watch/reject decisions.
- `docs/plans/2026-06-12-stage32-policy-action-design.md`: Stage 3.2 design boundary.
- `docs/stage3_runtime_mvp_design.md`: Stage 3 MVP design for action runtime, scene provider, safety runtime, and episode recorder.
- `docs/stage2_backend_diagnostics.md`: mock-vs-PyBullet diagnostics and calibration details.
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
- `PolicyActionSequence` is defined as a frozen dataclass with JSON load/save and conversion to runtime actions.
- Dataset adapters follow a Protocol-based pattern (`dataset_adapters/base.py`); `MiniSequenceAdapter` and `LeRobotStyleAdapter` are implemented for local samples.
- The dataset adapter registry is a simple dict mapping; there is no pluggable discovery or external registration yet.
- Visual sandbox artifacts are static reports and PNGs generated from episode logs; this is not an interactive simulator or hardware controller.
- Future agent tools must call application services through a tool boundary and must not call robot device execution methods directly.

## Next Recommended Step

Stage 3.7 Agent Context Runtime is complete. The next stage is **Stage 3.8 Diagnostic-only LLM Agent** (only after agent context is stable).

Stage 3.7 provides a deterministic, LLM-free diagnostic evidence packaging layer. Any future LLM integration must consume the agent context output and must not alter safety decisions or execute robot actions.

### Stage 3.7 Boundaries (carried forward)

- Do not call DeepSeek, OpenAI, or any LLM.
- Do not make approve/reject decisions.
- Do not modify or execute robot actions.
- Do not connect RealMan SDK, ROS2, MoveIt, or VLA.
- Do not build a web UI or multi-agent logic.

### Completion Standard

A user can run sandbox with metrics DB, list an episode, then build a deterministic diagnostic context package:

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

Expected outputs:
- `diagnostic_context.json`
- `diagnostic_context.md`

### Previously Completed

1. ✅ Stage 3.2 PolicyAction / PolicyActionSequence — done.
2. ✅ Stage 3.3 sequence runtime — done.
3. ✅ Stage 3.4 mini_sequence + lerobot_style adapters, service, CLI, smoke — done.
4. ✅ Stage 3.5 episode loader, summary report, visual artifacts, sandbox service + CLI — done.
5. ✅ Stage 3.6 SQLite schema, repository, episode ingest, metrics service, CLI — done.
6. ✅ Stage 3.7 Agent Context Runtime: models, builder, renderer, service, CLI — done.
