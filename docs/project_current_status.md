# Project Current Status

RobotArmSafetyReviewer is currently in **Stage 3.0 Cleanup**.

This stage stabilizes the Stage 3 runtime MVP and closes historical documentation and technical-debt gaps before adding agent tools, PyBullet robot-device execution, or hardware-facing adapters.

## Completed Scope

- Stage 1 deterministic safety gate.
- Stage 1.5 benchmark, scorer, replay, and report loop.
- Stage 2 PyBullet backend diagnostics.
- Stage 2.6 documentation and explicit evaluator metadata cleanup.
- Stage 3 MVP runtime action loop.

## Current Focus

- Runtime stabilization.
- Legacy docs cleanup.
- Execution result propagation.
- Episode schema hardening.
- CLI and test cleanup.

## Current Verification Snapshot

Recent known-good verification on the local `robotarm-pybullet` conda environment:

```text
pytest -q
108 passed

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

1. Finish Stage 3.0 cleanup with stable tests and docs.
2. Add an agent-ready diagnostic tool layer only after the runtime loop stays measurable.
3. Extend the runtime from one-step replay to small episode batches with stable metrics.
4. Defer RealMan SDK, ROS2, MoveIt, VLA, and LLM agent control until the runtime metrics and failure traces are stable.
