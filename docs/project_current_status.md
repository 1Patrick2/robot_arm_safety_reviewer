# Project Current Status

RobotArmSafetyReviewer is currently in **Stage 3 MVP runtime validation**.

The project has already completed the Stage 1/1.5 deterministic safety-gate loop, the Stage 2 PyBullet diagnostics loop, and a minimal Stage 3 LeRobot-style safety runtime. The current focus is to keep the runtime small, measurable, and audit-friendly before adding larger agent or hardware integrations.

## Completed Scope

- Stage 1: deterministic robot-arm safety gate.
- Stage 1.5: benchmark, scorer, replay, and report loop.
- Stage 2.1: simulation backend abstraction.
- Stage 2.2: mock RealMan-style URDF asset.
- Stage 2.3: minimal PyBullet backend.
- Stage 2.4: mock-vs-PyBullet backend comparison.
- Stage 2.5A: PyBullet closest-point collision geometry.
- Stage 2.5B: PyBullet geometry diagnostics.
- Stage 2.5C: URDF-vs-mock calibration reporting.
- Stage 2.6: project architecture docs, core function map, interview notes, and explicit evaluator backend metadata outcome.
- Stage 3 MVP: robot device adapter, mock RealMan device, replay action source, static scene provider, safety runtime step loop, episode recorder, and runtime demo CLI.

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
decision=approve, executed=true

python -m cli.run_runtime_demo --task bench/sim_robot_arm/near_miss_clearance_001 --backend mock --json
decision=manual_review, executed=false

python -m cli.run_runtime_demo --task bench/sim_robot_arm/obstacle_collision_001 --backend mock --json
decision=reject, executed=false
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
- `docs/stage3_runtime_mvp_design.md`: Stage 3 MVP design for action runtime, scene provider, safety runtime, and episode recorder.
- `docs/plans/stage3_runtime_mvp.md`: implementation plan and verification checklist for the Stage 3 MVP.
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

## Next Recommended Step

Do not jump directly into a large Agent or RealMan SDK integration.

Recommended order:

1. Keep Stage 3 scoped as a safety interposer, not a LeRobot clone.
2. Add an agent-ready diagnostic tool layer only after the runtime loop stays measurable.
3. Extend the runtime from one-step replay to small episode batches with stable metrics.
4. Defer RealMan SDK, ROS2, MoveIt, VLA, and LLM agent control until the runtime metrics and failure traces are stable.
