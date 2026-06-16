# RobotArmSafetyReviewer Project Architecture

## 1. Project Positioning

RobotArmSafetyReviewer is a simulation-first pre-execution safety reviewer for 6-DOF robot-arm joint-space commands.

It is not a path planner, a MoveIt replacement, a RealMan digital twin, or an LLM-controlled robot policy. Its job is narrower and safer: given a structured scene and a candidate joint command, it reviews whether the command should be approved, rejected, or sent to manual review.

The core project value is turning "is this robot-arm command safe?" into a deterministic, replayable, benchmarkable, and reportable engineering workflow.

## 2. Inputs And Outputs

Inputs:

- `scene.json`: robot model, obstacles, and safety thresholds.
- `command.json`: current joints, target joints, speed, and command metadata.

Core output:

- `SafetyResult`: decision, risk level, clearance, worst step, closest link/obstacle, violations, and evidence.

Operational outputs:

- replayable execution log JSON;
- benchmark scoring summary;
- Markdown safety report;
- backend comparison report;
- PyBullet geometry diagnostics;
- URDF-vs-mock calibration report.
- Stage 3 runtime episode metadata and step JSONL.

## 3. Core Call Chain

Review-only flow:

```text
cli.review_command
  -> gateway.safety_gate.review_only
    -> Scene.from_json
    -> JointCommand.from_json
    -> sim.backend_factory.create_backend
    -> robot_safety.evaluator.evaluate_joint_command_with_metadata
      -> interpolate_joint_trajectory
      -> compute_max_joint_delta
      -> check_trajectory_joint_limits
      -> backend.replay_joint_trajectory
      -> classify_risk_level
      -> make_decision
      -> SafetyResult + backend metadata
    -> build_execution_log
    -> write_execution_log
```

Execute-if-safe flow:

```text
cli.execute_if_safe
  -> gateway.safety_gate.execute_if_safe
    -> run the same safety review flow
    -> if decision == approve:
         RobotAdapter.execute_joint_move
       else:
         skip execution
    -> build_execution_log
```

Benchmark flow:

```text
cli.run_benchmark
  -> robot_safety.benchmark.run_benchmark
    -> review each benchmark task
    -> write execution logs
    -> robot_safety.scorer.score_execution_log
    -> optional JSON / Markdown summary
```

Backend comparison and diagnostics flow:

```text
cli.compare_backends
  -> run the same tasks through mock and PyBullet backends
  -> reports.backend_comparison
  -> compare decision, risk, clearance band, attribution, and strict match

cli.diagnose_backend_geometry
  -> sim.pybullet_diagnostics
  -> per-step closest-point geometry observations

cli.calibrate_urdf_geometry
  -> sim.urdf_calibration
  -> compare PyBullet URDF geometry with mock kinematic segments
```

Runtime action flow:

```text
RobotObservation + RobotAction
  -> robot_runtime.safety_runtime.SafetyRuntime.step
    -> SceneProvider.get_scene
    -> action_to_joint_command
    -> robot_safety.evaluator.evaluate_joint_command_with_metadata
      -> SafetyResult + backend metadata
    -> if decision == approve:
         RobotDeviceAdapter.send_action
         RuntimeExecutionResult
       else:
         blocked_reason
    -> EpisodeRecorder.record_step
```

Application service flow:

```text
CLI / Agent Tool / Python API / Future Web API
  -> application service layer
    -> gateway / robot_runtime / sim / reports
```

Stage 3.1 introduces this application layer so new entry points do not reassemble `ActionSource`, `SceneProvider`, backend, robot device, recorder, and runtime objects independently.

## 4. Layer Responsibilities

Data model layer:

- Defines typed project contracts: scene, robot model, obstacles, command, violations, and safety result.
- Keeps CLI, gateway, evaluator, reports, and tests using the same schema.

Safety computation layer:

- Interpolates joint-space trajectories.
- Computes max joint delta.
- Checks joint limits.
- Classifies deterministic risk and decision outcomes.

Simulation backend layer:

- Hides backend-specific geometry implementation behind `SimulationBackend`.
- Allows the evaluator to use either deterministic mock geometry or PyBullet without changing safety-result logic.

Gateway layer:

- Defines the safety boundary.
- `review_only` never executes commands.
- `execute_if_safe` executes only after an `approve` decision.
- Writes replayable logs for auditing and reports.

Benchmark and report layer:

- Runs structured tasks.
- Scores actual safety behavior against expected contracts.
- Produces JSON/Markdown summaries and human-readable reports.

Diagnostics layer:

- Explains backend disagreement.
- Provides PyBullet closest-point observations and URDF-vs-mock calibration evidence.

Runtime layer:

- Adapts robot observations and proposed actions into the existing safety-review contract.
- Sends actions to a robot device only after an `approve` decision.
- Preserves runtime execution results, blocked reasons, backend metadata, and episode traceability.
- Keeps Stage 3 scoped as a safety interposer rather than a LeRobot clone or planner.

Application service layer:

- Owns reusable orchestration that should not live inside CLI files.
- `application.runtime_service.run_runtime_task` builds and runs one runtime task.
- `application.review_service.review_command` wraps review-only safety-gate execution.
- `application.sequence_runtime_service.run_sequence_runtime` runs multi-step policy action sequences through the safety runtime.
- `application.dataset_service.dataset_list` and `dataset_export_sequence` wrap dataset adapter operations.
- Lets legacy CLI, unified CLI, future batch jobs, and agent tools reuse the same service functions.

CLI output layer:

- Owns JSON and text formatting for application result objects.
- Keeps CLI command modules focused on argument parsing, request construction, and service calls.
- Preserves legacy CLI output contracts while allowing future commands to share the same formatting helpers.

## 5. Application Boundary Rules

Allowed dependency direction:

```text
CLI / Future Agent Tool / Future Batch Job
  -> application
    -> robot_runtime / robot_safety / sim / gateway / reports / dataset_adapters
```

The application layer may import lower-level runtime, safety, simulation, gateway, report, dataset adapter, and future runtime database packages.

Lower-level packages must not import `application`, future `agent`, or future `robot_tools` packages. This keeps deterministic safety and runtime code reusable outside any CLI or agent surface.

Future agent tools must call:

```text
agent diagnostic surface -> robot_tools -> application
```

Agents must not directly call `RobotDeviceAdapter.send_action()` or decide `approve`, `manual_review`, or `reject`. Safety decisions remain deterministic and application services remain the execution boundary.

## 6. Mock Backend Vs PyBullet Backend

Mock backend:

- deterministic regression baseline;
- uses simplified 6-DOF FK and segment-sphere clearance;
- fast and stable for tests and benchmark scoring;
- intentionally not a calibrated real robot model.

PyBullet backend:

- diagnostic simulation backend;
- replays the URDF model in PyBullet `DIRECT` mode;
- uses closest-point queries over URDF collision geometry and sphere obstacles;
- exposes backend metadata, checked links, closest-point search distance, and geometry attribution.

Expected difference:

- Mock and PyBullet do not need to match exact clearance values.
- The project compares decision, risk, clearance band, attribution, and strict match separately.
- Remaining disagreements are documented in `docs/stage2_backend_diagnostics.md`.

## 7. `review_only` Vs `execute_if_safe`

`review_only`:

- reviews a command;
- writes a log;
- never calls `RobotAdapter`;
- useful for benchmark, audit, diagnostics, and report generation.

`execute_if_safe`:

- runs the same safety review first;
- calls `RobotAdapter.execute_joint_move` only when the decision is `approve`;
- records adapter success or failure;
- rejects or manual-review commands never reach execution.

This is the main safety-gate boundary: deterministic tools decide whether execution is allowed before any robot adapter is called.

## 8. Benchmark / Scorer / Report / Diagnostics Relationship

Benchmark:

- defines structured tasks under `bench/sim_robot_arm`;
- runs repeated safety reviews under the same contract.

Scorer:

- compares execution logs with each task's expected result;
- checks decision, risk, violations, clearance, and execution behavior.

Report:

- turns a single execution log into a human-readable safety report;
- includes safety decision, violations, evidence, execution status, and backend metadata.

Diagnostics:

- explain why backends agree or disagree;
- are not the primary safety decision mechanism;
- help improve URDF geometry, expected contracts, and future visualization.

## 9. Current Boundary

Implemented:

- deterministic safety gate;
- replayable logs;
- benchmark/scorer loop;
- mock backend;
- PyBullet backend;
- backend comparison;
- geometry diagnostics;
- URDF-vs-mock calibration.
- Stage 3 runtime action loop;
- runtime execution-result propagation;
- runtime episode metadata and step JSONL logs;
- runtime demo CLI;
- Stage 3.2 PolicyAction and PolicyActionSequence models;
- Stage 3.3 sequence runtime for multi-step policy action execution;
- application runtime/review/sequence_runtime/dataset services;
- unified CLI entry point for runtime, review, sequence, and dataset commands;
- shared CLI output formatting for all result types;
- Stage 3.4 DatasetAdapter Protocol, MiniSequenceAdapter, and LeRobotStyleAdapter.
- Stage 3.5 Visual Runtime Sandbox: episode loader, report, clearance curve, trajectory overview, sandbox service, sandbox CLI.
- Stage 3.6 Runtime Metrics DB: SQLite schema, repository, episode ingest, metrics service, metrics CLI.
- Stage 3.7 Agent Context Runtime: context models, metrics DB builder, JSON/Markdown renderer, context service, context CLI.

Not implemented:

- automatic obstacle avoidance;
- Cartesian planning or IK;
- self-collision;
- workspace boundary;
- velocity/acceleration safety;
- RealMan SDK execution;
- ROS2 / MoveIt integration;
- LLM safety decision making.

Stage 3.7 Agent Context Runtime is the current completed runtime boundary. It packages deterministic episode evidence for diagnostic review only; it does not make safety decisions, modify actions, or execute robot commands.
