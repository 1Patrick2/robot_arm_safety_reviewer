# Project Current Status

RobotArmSafetyReviewer has completed **Stage 3.5 Visual Runtime Sandbox**.

This stage introduces a visual sandbox layer that turns episode logs into static artifacts: Markdown summaries, clearance curve PNGs, and trajectory overview PNGs.

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

## Current Focus

- Stage 3.5 Visual Runtime Sandbox is stable and producing artifacts.
- Next: Stage 3.6 Runtime Metrics DB for structured episode metrics storage and query.
- No DeepSeek, RealMan SDK, ROS2, or large-scale dataset integration until metrics storage is stable.

## Current Verification Snapshot

Recent focused verification on the local `robotarm-pybullet` conda environment:

```text
python -m pytest tests/test_stage34_mini_sequence_adapter.py tests/test_stage34_lerobot_style_adapter.py tests/test_stage34_dataset_service.py tests/test_stage34_dataset_cli.py tests/test_stage34_dataset_to_sequence_runtime.py -q
25 passed

python -m pytest tests/test_stage33_sequence_runtime.py -q
7 passed
```

Run the current verification with:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage34_mini_sequence_adapter.py tests/test_stage34_lerobot_style_adapter.py tests/test_stage34_dataset_service.py tests/test_stage34_dataset_cli.py tests/test_stage34_dataset_to_sequence_runtime.py -q --basetemp .pytest_tmp\current
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
- The Stage 3 runtime currently executes one proposed action per `step()` call and records episode logs; it is not yet a multi-step policy rollout engine.
- Sequence runtime (`run_sequence_runtime`) runs multi-step sequences using the same SafetyRuntime loop internally.
- CLI output is centralized in `cli/output.py`; command modules should not duplicate result formatting.
- `PolicyActionSequence` is defined as a frozen dataclass with JSON load/save and conversion to runtime actions.
- Dataset adapters follow a Protocol-based pattern (`dataset_adapters/base.py`); only `MiniSequenceAdapter` exists so far.
- The dataset adapter registry is a simple dict mapping; there is no pluggable discovery or external registration yet.
- Future agent tools must call application services through a tool boundary and must not call robot device execution methods directly.

## Next Recommended Step

Stage 3.5 Visual Runtime Sandbox is stable. The next stage is Stage 3.6 Runtime Metrics DB.

Recommended order:

1. ✅ Stage 3.2 PolicyAction / PolicyActionSequence — done.
2. ✅ Stage 3.3 sequence runtime — done.
3. ✅ Stage 3.4 mini_sequence + lerobot_style adapters, service, CLI, smoke — done.
4. ✅ Stage 3.5 episode loader, summary report, visual artifacts, sandbox service + CLI — done.
5. Add Stage 3.6 Runtime Metrics DB for structured episode metrics.
6. Add diagnostic agent after metrics and failure traces are queryable.
7. Defer DeepSeek, RealMan SDK, ROS2 until runtime metrics and diagnostic agent are stable.
