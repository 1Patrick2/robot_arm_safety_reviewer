# Robot Action Safety Sandbox

[Chinese README](README.zh-CN.md)

Robot Action Safety Sandbox is a deterministic 3D robot-arm safety runtime. It checks candidate joint-space actions before execution, records replayable episode evidence, stores runtime metrics, and builds diagnostic context packages for review.

The project started as `RobotArmSafetyReviewer`. It is still a safety reviewer, not a motion planner. It must not silently modify trajectories, generate obstacle-avoiding paths, or let an LLM decide robot safety.

## Current Status

Current stage: **Stage 3.8 Diagnostic Runtime in progress**.

Completed scope:

- Stage 1: deterministic safety gate for joint-space commands.
- Stage 1.5: benchmark, scorer, replay, and report loop.
- Stage 2: backend abstraction, PyBullet diagnostics, mock-vs-PyBullet comparison, and URDF calibration diagnostics.
- Stage 3.1: application service layer, unified CLI, and shared output formatting.
- Stage 3.2: `PolicyAction` and `PolicyActionSequence`.
- Stage 3.3: multi-step sequence runtime through `SafetyRuntime`.
- Stage 3.4: dataset adapters for local `mini_sequence` and `lerobot_style` samples.
- Stage 3.5: visual sandbox artifacts from runtime episodes.
- Stage 3.6: SQLite runtime metrics database.
- Stage 3.7: deterministic agent context package generation from metrics DB records.
- Stage 3.8A: evidence correctness hardening (scene robot model, obstacle rendering, structured evidence data).
- Stage 3.8B: diagnostic tools (read-only context query layer).
- Stage 3.8C: deterministic diagnostic report (LLM-free).
- Stage 3.8D: diagnostic agent runner with safety boundary checker.
- Stage 3.8E: DeepSeek adapter (optional smoke-only, not part of deterministic safety path).

## Safety Boundary

- Safety decisions are deterministic: `approve`, `manual_review`, or `reject`.
- Only `approve` reaches `RobotDeviceAdapter.send_action()`.
- `manual_review` and `reject` are blocked and recorded.
- Agent context output is diagnostic evidence only. It must not approve, reject, modify, or execute robot actions.
- The mock backend and PyBullet backend are diagnostic simulation tools, not certified hardware validation.

Deferred:

- Full diagnostic CLI (`cli.main diagnostic report`, `cli.main diagnostic agent-run`).
- RealMan SDK / hardware execution.
- ROS2 / MoveIt.
- VLA or autonomous robot-control agent.
- Large remote dataset integration.

## Quick Start

Recommended Windows environment:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe --version
D:\miniforge3\envs\robotarm-pybullet\python.exe -c "import pybullet as p; print('pybullet ok')"
```

Run targeted tests with a project-local temp directory:

```powershell
New-Item -ItemType Directory -Force .pytest_tmp | Out-Null
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage37_agent_context_builder.py -q --basetemp .pytest_tmp\current
```

## Common Commands

### Review One Command

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main review ^
  --scene bench\sim_robot_arm\obstacle_collision_001\scene.json ^
  --command bench\sim_robot_arm\obstacle_collision_001\command.json ^
  --backend mock ^
  --log-dir logs ^
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

### Run Visual Sandbox With Metrics DB

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main sandbox run ^
  --sequence samples\policy_sequences\simple_safe_sequence.json ^
  --scene bench\sim_robot_arm\simple_joint_move_001\scene.json ^
  --backend mock ^
  --output-root output_reports\sandbox ^
  --metrics-db output_reports\runtime_metrics\runtime_metrics.db ^
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

### Query Runtime Metrics

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main metrics list-runs ^
  --db output_reports\runtime_metrics\runtime_metrics.db ^
  --json
```

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main metrics show-run ^
  --db output_reports\runtime_metrics\runtime_metrics.db ^
  --episode-id episode_xxx ^
  --json
```

### Build Diagnostic Agent Context

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main context build ^
  --db output_reports\runtime_metrics\runtime_metrics.db ^
  --episode-id episode_xxx ^
  --output-dir output_reports\agent_context\episode_xxx ^
  --json
```

Generated context artifacts:

```text
diagnostic_context.json
diagnostic_context.md
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
  -> visual reports
  -> runtime metrics DB
  -> diagnostic agent context package
```

Main modules:

```text
robot_safety/                 deterministic safety models, trajectory, collision, evaluator, scorer
sim/                          backend abstraction, mock backend, PyBullet backend, diagnostics
robot_runtime/                runtime actions, observations, devices, sequences, episode recorder/loader
dataset_adapters/             mini_sequence and local LeRobot-style adapters
runtime_db/                   SQLite schema, repository, and episode ingest
agent_context/                diagnostic context models, builder, and renderers
application/                  review, runtime, sequence, dataset, sandbox, metrics, and context services
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

## Project Docs

- [Current status](docs/project_current_status.md)
- [Project architecture](docs/project_architecture.md)
- [Core function map](docs/core_function_map.md)
- [Stage 2 backend diagnostics](docs/stage2_backend_diagnostics.md)
- [Windows PyBullet setup](docs/windows_pybullet_setup.md)
- [Interview notes](docs/interview_notes.md)
