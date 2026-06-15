# Robot Action Safety Sandbox

[中文说明](README.zh-CN.md)

Simulation-first safety sandbox for robot-arm policy actions.

This project started as `RobotArmSafetyReviewer` and has evolved into a lightweight runtime sandbox for robot action safety evaluation. It accepts candidate joint-space actions, reviews them with deterministic safety rules, executes only approved actions through a robot-device boundary, records episode logs, and generates runtime evidence artifacts.

It is not a planner, MoveIt replacement, Isaac replacement, LeRobot clone, VLA model, or autonomous robot-control agent.

## What It Does

- Reviews `current_joints -> target_joints` joint-space commands.
- Converts `PolicyActionSequence` inputs into runtime `RobotAction` steps.
- Supports `joint_target` and `delta_joint` policy actions.
- Runs deterministic safety review for joint limits, interpolated collision, clearance, and large motion risk.
- Returns `approve`, `manual_review`, or `reject`.
- Executes only approved actions through `RobotDeviceAdapter`.
- Blocks `manual_review` and `reject` steps.
- Records runtime episodes as `metadata.json` and `steps.jsonl`.
- Loads local dataset-style samples through dataset adapters.
- Generates visual sandbox artifacts: `episode_summary.md`, `clearance_curve.png`, and `trajectory_overview.png`.

## Current Stage

Current status: **Stage 3.5 Visual Runtime Sandbox completed**.

Completed stages:

- Stage 1: deterministic safety gate.
- Stage 1.5: benchmark, scorer, replay, and report loop.
- Stage 2: backend-agnostic review, PyBullet backend diagnostics, mock-vs-PyBullet comparison, and URDF calibration diagnostics.
- Stage 3.1: application service layer, unified CLI, and shared output formatting.
- Stage 3.2: `PolicyAction` and `PolicyActionSequence`.
- Stage 3.3: multi-step sequence runtime through `SafetyRuntime`.
- Stage 3.4: Dataset Adapter MVP with `mini_sequence` and local `lerobot_style` adapters.
- Stage 3.5: visual sandbox artifacts from runtime episodes.

Next recommended stage:

- Stage 3.6 Runtime Metrics DB: persist runs, steps, decisions, clearance, risky links/obstacles, and artifact paths into SQLite.

Deferred:

- DeepSeek diagnostic agent.
- RealMan SDK / hardware execution.
- ROS2 / MoveIt.
- VLA or autonomous robot-control agent.
- Large remote dataset integration.

## Safety Boundary

Safety decisions are deterministic. LLMs and future agents must not decide `approve`, `manual_review`, or `reject`.

Only `approve` reaches `RobotDeviceAdapter.send_action()`.

`manual_review` and `reject` are blocked and recorded.

The mock 6-DOF model and PyBullet backend are diagnostic simulation tools, not calibrated RealMan digital twins and not certified hardware validation.

## Quick Start

Recommended Windows environment:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe --version
D:\miniforge3\envs\robotarm-pybullet\python.exe -c "import pybullet as p; print('pybullet ok')"
```

Run focused tests with a project-local temp directory:

```powershell
New-Item -ItemType Directory -Force .pytest_tmp | Out-Null
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage33_sequence_runtime.py -q --basetemp .pytest_tmp\current
```

### Review One Command

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main review ^
  --scene bench\sim_robot_arm\obstacle_collision_001\scene.json ^
  --command bench\sim_robot_arm\obstacle_collision_001\command.json ^
  --backend mock ^
  --log-dir logs ^
  --json
```

### Run One Runtime Task

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main runtime run ^
  --task bench\sim_robot_arm\simple_joint_move_001 ^
  --backend mock ^
  --episode-root output_reports\runtime_demo ^
  --json
```

### Run A Policy Action Sequence

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main sequence run ^
  --sequence samples\policy_sequences\simple_safe_sequence.json ^
  --scene bench\sim_robot_arm\simple_joint_move_001\scene.json ^
  --backend mock ^
  --episode-root output_reports\sequence_runtime ^
  --json
```

Use `--continue-on-block` to keep recording later steps after a `manual_review` or `reject` decision.

### List Dataset Sequences

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main dataset list ^
  --adapter mini_sequence ^
  --source samples\policy_sequences ^
  --json
```

Local LeRobot-style sample:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main dataset list ^
  --adapter lerobot_style ^
  --source samples\lerobot_style ^
  --json
```

### Export A Dataset Sequence

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main dataset export-sequence ^
  --adapter mini_sequence ^
  --source samples\policy_sequences ^
  --sequence-id simple_safe_sequence_001 ^
  --output output_reports\exported_sequence.json ^
  --json
```

### Run Visual Sandbox

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main sandbox run ^
  --sequence samples\policy_sequences\simple_safe_sequence.json ^
  --scene bench\sim_robot_arm\simple_joint_move_001\scene.json ^
  --backend mock ^
  --output-root output_reports\sandbox ^
  --json
```

Generated episode artifacts:

```text
metadata.json
steps.jsonl
episode_summary.md
clearance_curve.png
trajectory_overview.png
```

## Architecture

```text
PolicyActionSequence / dataset sample
  -> application service
  -> SafetyRuntime.step()
  -> deterministic safety review
  -> approve: RobotDeviceAdapter.send_action()
  -> manual_review / reject: block execution
  -> EpisodeRecorder
  -> reports / visual artifacts
```

Main modules:

```text
robot_safety/                 deterministic safety models, trajectory, collision, evaluator, scorer
sim/                          backend abstraction, mock backend, PyBullet backend, diagnostics
robot_runtime/                runtime actions, observations, devices, sequences, episode recorder/loader
dataset_adapters/             mini_sequence and local LeRobot-style adapters
application/                  runtime, sequence, dataset, review, and sandbox service layer
cli/                          unified command-line interface
reports/                      safety reports and runtime visual artifacts
gateway/                      legacy safety gate and replayable execution logs
robots/                       low-level mock RealMan-compatible adapter
```

## Benchmark Tasks

Stage 1 includes eight simulation tasks:

```text
simple_joint_move_001          approve
joint_limit_violation_001      reject
obstacle_collision_001         reject
mid_trajectory_collision_001   reject, nonzero worst-step collision
near_miss_clearance_001        manual_review
long_motion_delta_risk_001     manual_review
multi_obstacle_clearance_001   approve
invalid_command_001            reject
```

`obstacle_collision_001` validates initial-state collision rejection. `mid_trajectory_collision_001` validates a separate mid-trajectory collision case.

## Project Docs

- [Current status](docs/project_current_status.md)
- [Project architecture](docs/project_architecture.md)
- [Core function map](docs/core_function_map.md)
- [Stage 2 backend diagnostics](docs/stage2_backend_diagnostics.md)
- [Stage 3 runtime MVP design](docs/stage3_runtime_mvp_design.md)
- [LeRobot interface study](docs/lerobot_interface_study.md)
- [Windows PyBullet setup](docs/windows_pybullet_setup.md)
- [Interview notes](docs/interview_notes.md)

## Roadmap

Near term:

- Stage 3.6 Runtime Metrics DB.
- Batch metrics summaries over dataset-backed sequence runs.
- Diagnostic-only agent tools after metrics and failure traces are queryable.

Later:

- PyBulletRobotDevice or richer simulation device boundary.
- RealMan SDK study, dry-run, shadow mode, then limited safe execution.
- Workspace, speed, acceleration, and self-collision safety rules.
- Larger dataset adapters, kept optional and test-skippable.
