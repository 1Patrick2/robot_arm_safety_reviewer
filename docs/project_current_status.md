# Project Current Status

RobotArmSafetyReviewer is currently entering **Stage 3.4 Dataset Adapter MVP** after closing the Stage 3.3 sequence runtime loop.

This stage introduces the Dataset Adapter MVP: a Protocol-based abstraction for loading PolicyActionSequence objects from local sources, backed by a MiniSequenceAdapter plus application service and CLI wiring.

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
- Stage 3.4 Dataset Adapter MVP: DatasetAdapter Protocol, MiniSequenceAdapter for samples/policy_sequences, dataset service, and dataset CLI.

## Current Focus

- Dataset Adapter Protocol and MiniSequenceAdapter are stable.
- Next dataset adapter variants (LeRobot-style local adapter).
- Visual Runtime Sandbox for episode trajectory and clearance visualization.
- Keeping future batch jobs, CLI commands, and agent tools using the same application service boundary.
- No DeepSeek, RealMan SDK, ROS2, or large-scale dataset integration until dataset-backed runtime and visual artifacts are stable.

## Current Verification Snapshot

Recent known-good verification on the local `robotarm-pybullet` conda environment:

```text
pytest -q
106 passed

python -m cli.run_benchmark --backend pybullet --mode smoke --bench bench/sim_robot_arm
8 completed, 0 runtime errors

python -m cli.compare_backends --bench bench/sim_robot_arm --backends mock pybullet
decision_matches=8, risk_matches=8, strict_matches=6, backend_errors=0

python -m cli.run_runtime_demo --task bench/sim_robot_arm/simple_joint_move_001 --backend mock --json
decision=approve, executed=true, execution_result.success=true

python -m cli.run_runtime_demo --task bench/sim_robot_arm/near_miss_clearance_001 --backend mock --json
decision=manual_review, executed=false, blocked_reason=manual_review_required

python -m cli.run_runtime_demo --task bench/sim_robot_arm/obstacle_collision_001 --backend mock --json
decision=reject, executed=false, blocked_reason=rejected_by_safety_gate

python -m cli.main runtime run --task bench/sim_robot_arm/simple_joint_move_001 --backend mock --json
decision=approve, executed=true

python -m cli.main review --scene bench/sim_robot_arm/obstacle_collision_001/scene.json --command bench/sim_robot_arm/obstacle_collision_001/command.json --backend mock --json
decision=reject
```

Run the current verification with:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp\current
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

Do not jump directly into a large Agent or RealMan SDK integration.

Recommended order:

1. ✅ Stage 3.2 `PolicyAction` and `PolicyActionSequence` — done.
2. ✅ Stage 3.3 sequence runtime — done.
3. ✅ Stage 3.4 mini_sequence adapter, service, and CLI — done.
4. Add a local LeRobot-style dataset adapter after the mini adapter contract is stable.
5. Add visual sandbox artifacts and runtime metrics storage before any diagnostic agent.
6. Add a diagnostic-only DeepSeek agent after metrics and failure traces are queryable.
7. Defer RealMan SDK, ROS2, MoveIt, VLA, and LLM agent control until the runtime metrics and failure traces are stable.
