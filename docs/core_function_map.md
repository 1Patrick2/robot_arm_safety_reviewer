# Core Function Map

This document is a quick code-reading map for RobotArmSafetyReviewer. It lists the main files, the functions or classes worth reading first, and the role each one plays in the safety-review workflow.

| Layer | File | Core Function / Class | Purpose |
|---|---|---|---|
| Data model | `robot_safety/models.py` | `Scene`, `JointCommand`, `SafetyResult`, `Violation` | Defines the structured input/output contract used across CLI, gateway, evaluator, benchmark, and reports. |
| Trajectory | `robot_safety/trajectory.py` | `interpolate_joint_trajectory` | Converts `current_joints -> target_joints` into an interpolated joint-space trajectory for whole-path checking. |
| Trajectory | `robot_safety/trajectory.py` | `compute_max_joint_delta` | Measures large motion delta risk for manual-review decisions. |
| Mock FK | `robot_safety/kinematics.py` | `forward_kinematics_6dof` | Builds simplified mock robot link points for deterministic segment-based collision checking. |
| Mock collision | `robot_safety/collision.py` | `check_trajectory_collision` | Checks link-sphere collision and clearance along the interpolated trajectory. |
| Safety rules | `robot_safety/safety_rules.py` | `check_trajectory_joint_limits` | Validates every interpolated joint state against configured joint limits. |
| Safety rules | `robot_safety/safety_rules.py` | `classify_risk_level`, `make_decision` | Converts geometry and rule signals into `low/medium/high` and `approve/manual_review/reject`. |
| Evaluator | `robot_safety/evaluator.py` | `evaluate_joint_command` | Backward-compatible review entry point returning only `SafetyResult`. |
| Evaluator | `robot_safety/evaluator.py` | `evaluate_joint_command_with_metadata` | Explicit review entry point returning `SafetyResult` plus backend metadata. |
| Backend contract | `sim/base.py` | `SimulationBackend`, `BackendReviewResult` | Defines the common backend protocol and result shape. |
| Backend factory | `sim/backend_factory.py` | `create_backend` | Creates `mock` or `pybullet` backend instances from CLI/gateway options. |
| Mock backend | `sim/mock_backend.py` | `MockGeometryBackend.replay_joint_trajectory` | Preserves deterministic Stage 1.5 mock geometry behavior behind the backend interface. |
| PyBullet backend | `sim/pybullet_backend.py` | `PyBulletBackend.replay_joint_trajectory` | Replays trajectories through URDF collision geometry and closest-point queries. |
| Gateway | `gateway/safety_gate.py` | `review_only` | Reviews a command and writes a replayable log without execution. |
| Gateway | `gateway/safety_gate.py` | `execute_if_safe` | Runs review first and executes through `RobotAdapter` only after an `approve` decision. |
| Logs | `gateway/execution_logger.py` | `build_execution_log`, `write_execution_log` | Builds and writes replayable execution logs. |
| Replay | `gateway/replay.py` | `replay_log` | Recomputes safety review from a log to check deterministic consistency. |
| Robot adapter | `robots/base.py` | `RobotAdapter`, `RobotExecutionResult` | Defines the execution adapter boundary. |
| Mock robot adapter | `robots/mock_realman_6dof.py` | `MockRealMan6DoFAdapter.execute_joint_move` | Simulates approved command execution in memory. |
| Runtime model | `robot_runtime/types.py` | `RobotObservation`, `RobotAction`, `RuntimeExecutionResult`, `RuntimeStepResult` | Defines the Stage 3 runtime observation, action, execution, and step-result contracts. |
| Runtime device | `robot_runtime/device.py` | `RobotDeviceAdapter` | Defines the runtime-facing robot device protocol. |
| Runtime action source | `robot_runtime/action_source.py` | `ReplayActionSource` | Converts benchmark command JSON into replayable runtime actions. |
| Runtime scene provider | `robot_runtime/scene_provider.py` | `StaticSceneProvider` | Supplies static benchmark scenes to the runtime loop. |
| Runtime loop | `robot_runtime/safety_runtime.py` | `SafetyRuntime.step` | Reviews a proposed runtime action and sends it to the robot only after an `approve` decision. |
| Runtime recorder | `robot_runtime/episode_recorder.py` | `EpisodeRecorder` | Writes Stage 3 runtime metadata and step JSONL logs. |
| Runtime adapter | `robot_runtime/adapters/mock_realman_device.py` | `MockRealManDevice` | Wraps the Stage 1 mock robot adapter behind the Stage 3 runtime device protocol. |
| Benchmark | `robot_safety/benchmark.py` | `run_benchmark` | Discovers benchmark tasks, runs reviews, writes logs, and builds summaries. |
| Scorer | `robot_safety/scorer.py` | `score_execution_log` | Compares actual logs with expected task contracts. |
| Report | `reports/report_writer.py` | `build_markdown_report` | Converts one execution log into a human-readable Markdown safety report. |
| Backend comparison | `reports/backend_comparison.py` | `compare_backends` | Runs the same benchmark tasks across mock/PyBullet and summarizes decision, risk, clearance-band, attribution, and strict-match metrics. |
| PyBullet diagnostics | `sim/pybullet_diagnostics.py` | `diagnose_task_geometry` | Emits per-step PyBullet closest-point geometry diagnostics. |
| URDF calibration | `sim/urdf_calibration.py` | `calibrate_task_geometry` | Compares PyBullet URDF geometry observations with mock geometry observations. |
| CLI | `cli/review_command.py` | `main` | CLI entry point for review-only command checks. |
| CLI | `cli/execute_if_safe.py` | `main` | CLI entry point for safety-gated execution. |
| CLI | `cli/run_benchmark.py` | `main` | CLI entry point for benchmark execution. |
| CLI | `cli/compare_backends.py` | `main` | CLI entry point for backend comparison. |
| CLI | `cli/diagnose_backend_geometry.py` | `main` | CLI entry point for PyBullet geometry diagnostics. |
| CLI | `cli/calibrate_urdf_geometry.py` | `main` | CLI entry point for URDF-vs-mock calibration. |
| CLI | `cli/run_runtime_demo.py` | `main` | CLI entry point for one-step Stage 3 runtime demos. |

Suggested reading order:

1. `robot_safety/models.py`
2. `robot_safety/evaluator.py`
3. `sim/base.py`, `sim/mock_backend.py`, `sim/pybullet_backend.py`
4. `gateway/safety_gate.py`, `gateway/execution_logger.py`
5. `robot_safety/benchmark.py`, `robot_safety/scorer.py`
6. `reports/backend_comparison.py`
7. `sim/pybullet_diagnostics.py`, `sim/urdf_calibration.py`
8. `robot_runtime/types.py`, `robot_runtime/safety_runtime.py`, `robot_runtime/episode_recorder.py`
