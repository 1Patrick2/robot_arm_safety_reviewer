# Project Current Status

RobotArmSafetyReviewer is currently entering **Stage 3.2 PolicyAction Interface** after closing the Stage 3.1 application foundation.

This stage extracts reusable application services from one-off CLI orchestration and adds a unified CLI entry point before adding batch jobs, agent tools, PyBullet robot-device execution, or hardware-facing adapters.

## Completed Scope

- Stage 1 deterministic safety gate.
- Stage 1.5 benchmark, scorer, replay, and report loop.
- Stage 2 PyBullet backend diagnostics.
- Stage 2.6 documentation and explicit evaluator metadata cleanup.
- Stage 3 MVP runtime action loop.
- Stage 3.0 runtime cleanup: execution-result propagation, episode schema hardening, and CLI safety checks.

## Current Focus

- Application service layer.
- Shared application result, artifact, and context envelope.
- Unified CLI entry point.
- Legacy CLI compatibility wrappers.
- Shared CLI output formatting.
- Service-level tests that do not rely on CLI as the only entry point.
- Keeping future batch and agent tools from duplicating runtime assembly logic.
- Boundary docs and pattern-first agent research docs.
- Stage 3.2 policy action model and local policy sequence fixtures.

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
- CLI output is centralized in `cli/output.py`; command modules should not duplicate result formatting.
- `PolicyActionSequence` can be loaded from JSON, but sequence execution is not implemented yet.
- Future agent tools must call application services through a tool boundary and must not call robot device execution methods directly.

## Next Recommended Step

Do not jump directly into a large Agent or RealMan SDK integration.

Recommended order:

1. Add Stage 3.2 `PolicyAction` and `PolicyActionSequence`.
2. Add Stage 3.3 sequence runtime for multi-step policy action execution.
3. Add Stage 3.4 dataset adapters after the internal sequence contract is stable.
4. Add visual sandbox artifacts and runtime metrics storage before any diagnostic agent.
5. Add a diagnostic-only DeepSeek agent after metrics and failure traces are queryable.
6. Defer RealMan SDK, ROS2, MoveIt, VLA, and LLM agent control until the runtime metrics and failure traces are stable.
