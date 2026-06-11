
# RobotArmSafetyReviewer

[中文说明](README.zh-CN.md)

Simulation-first safety middleware for 6-DOF robot arm joint-space commands.

RobotArmSafetyReviewer reviews candidate robot arm commands before execution by checking joint limits, interpolated trajectory collision, minimum clearance, and large joint-motion risk. It outputs `approve`, `manual_review`, or `reject`, then writes replayable logs and human-readable safety reports.

Project docs:

- [Project architecture](docs/project_architecture.md)
- [Core function map](docs/core_function_map.md)
- [Interview notes](docs/interview_notes.md)
- [LeRobot interface study](docs/lerobot_interface_study.md)
- [Stage 3 runtime MVP design](docs/stage3_runtime_mvp_design.md)
- [Current status](docs/project_current_status.md)
- [Stage 2 backend diagnostics](docs/stage2_backend_diagnostics.md)

## What It Does

- Reviews `current_joints -> target_joints` joint-space commands.
- Interpolates deterministic 6-DOF joint trajectories.
- Runs a simplified mock 6-DOF forward-kinematics chain.
- Checks joint limits, link-sphere collision, clearance, and joint delta.
- Produces structured `SafetyResult` JSON.
- Writes replayable execution logs.
- Scores benchmark tasks against structured expected contracts.
- Replays logs to verify deterministic safety-review consistency.
- Generates Markdown safety reports.
- Simulates execution through `MockRealMan6DoFAdapter` only when approved.

## Current Stage

Stage 1 MVP is focused on a deterministic safety gate. Stage 1.5 adds a small benchmark/scorer/replay loop around that gate.

Stage 2 adds backend-agnostic safety review and PyBullet diagnostics:

- `SimulationBackend` abstraction
- `MockGeometryBackend` deterministic baseline
- `PyBulletBackend` with URDF kinematic replay
- PyBullet closest-point collision geometry over URDF collision bodies
- backend metadata in logs and reports
- backend smoke benchmark
- mock-vs-PyBullet comparison
- PyBullet geometry diagnostics
- URDF-vs-mock calibration reporting

Stage 3 adds a minimal runtime safety interposer:

- `RobotObservation` / `RobotAction` runtime contracts
- `RobotDeviceAdapter` boundary and `MockRealManDevice`
- replay action source and static scene provider
- `SafetyRuntime.step()` approve/manual_review/reject loop
- runtime execution-result propagation
- episode metadata and step JSONL recorder
- one-step runtime demo CLI

Stage 1.5 status:

```text
Benchmark: 8 / 8 passed
Decision accuracy: 100%
Risk accuracy: 100%
Violation match: 100%
Gateway execution match: 100%
Replay consistency: passed
```

Included:

- mock 6-DOF robot model
- backend-agnostic simulation review interface
- optional PyBullet URDF backend
- joint-space command review
- sphere obstacle collision
- `approve / manual_review / reject` decision
- execution log
- benchmark runner and scorer
- log replay consistency check
- Markdown report
- optional matplotlib 3D plot
- mock RealMan-compatible adapter
- backend comparison and calibration diagnostics

Not included in Stage 1:

- LLM / AgentRuntime
- OpenAI, DeepSeek, or online APIs
- real robot hardware control
- ROS2 or MoveIt integration
- calibrated RealMan kinematics
- full Cartesian IK or grasp planning
- learned control policy or VLA reproduction

## Important Modeling Boundary

The current forward kinematics is **not** a calibrated RealMan kinematic model. It is a deterministic mock 6-DOF serial chain used to validate the safety review pipeline. Future versions can replace this layer with a PyBullet URDF backend, RealMan SDK state snapshots, or ROS2 / MoveIt-style planning scenes while keeping the safety-result schema, logs, reports, and gateway structure.

Stage 2 includes a PyBullet URDF backend, but it is still a simulation diagnostic backend rather than a certified real-robot model. PyBullet uses URDF collision geometry and closest-point queries; the mock backend uses simplified FK segments. Differences between the two are expected and documented in `docs/stage2_backend_diagnostics.md`.

Stage 1 uses linear joint-space interpolation, not time-parameterized trajectory planning. Command `speed` is recorded in logs and reports, but dynamic velocity/acceleration safety is future work.

Self-collision is not implemented in Stage 1. The result explicitly reports whether self-collision was checked.

`MockRealMan6DoFAdapter` is not a physics simulator or a RealMan digital twin. It is an in-memory `RobotAdapter` implementation used to validate the safety-gate workflow, execution boundary, adapter result logging, and CLI behavior.

RobotArmSafetyReviewer never executes commands that are rejected or require manual review. Only commands with an `approve` decision can reach the RobotAdapter execution layer.

## Environment Setup

On Windows, the recommended project environment is `micromamba` with Python 3.10 and `pybullet` from `conda-forge`. Avoid installing PyBullet into a global Windows Python 3.12 environment with `pip`, because it may fall back to a source build and require Microsoft C++ Build Tools.

Detailed Windows setup and troubleshooting notes are in [`docs/windows_pybullet_setup.md`](docs/windows_pybullet_setup.md).

Create the environment:

```powershell
$env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"
D:\YJSXueXi\Software\micromamba\micromamba.exe create -n robotarm-pybullet -c conda-forge python=3.10 pybullet pytest matplotlib-base -y
```

If NumPy or Matplotlib crashes with the default native math stack, switch the environment to OpenBLAS:

```powershell
D:\YJSXueXi\Software\micromamba\micromamba.exe install -n robotarm-pybullet -c conda-forge "libblas=*=*openblas" -y
```

Run commands inside the environment without activating it:

```powershell
$env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"
D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python --version
D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -c "import pybullet as p; print('pybullet ok')"
```

If pytest cannot access the default Windows temp directory, use a project-local temp directory:

```powershell
New-Item -ItemType Directory -Force .pytest_tmp | Out-Null
$env:TEMP="$PWD\.pytest_tmp"
$env:TMP="$PWD\.pytest_tmp"
```

Then run tests:

```powershell
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp/current
```

`requirements-sim.txt` lists the simulation-only dependency for pip-based Linux or WSL environments. On Windows, prefer `conda-forge` for `pybullet`.

## Quick Start

Use a Python environment with `pytest`. `matplotlib-base` is optional and only needed for PNG visualization.

Run tests:

```bash
python -m pytest -v
```

Review a command without simulated execution:

```bash
python -m cli.review_command ^
  --scene bench\sim_robot_arm\obstacle_collision_001\scene.json ^
  --command bench\sim_robot_arm\obstacle_collision_001\command.json ^
  --log-dir logs
```

Example output:

```text
Decision: reject
Risk Level: high
Min Clearance: -0.105
Closest Link: link_3
Closest Obstacle: sphere_01
Worst Step: 0
Log Path: logs\exec_YYYYMMDD_HHMMSS_xxxxxxxx.json
```

This example is an initial-state collision case: the command is rejected because `link_3` overlaps `sphere_01` at `worst_step = 0`, with `min_clearance = -0.105 m`. It validates environment-collision detection and fail-safe rejection, not mid-trajectory collision semantics.

Review and simulate execution only if approved:

```bash
python -m cli.execute_if_safe ^
  --scene bench\sim_robot_arm\simple_joint_move_001\scene.json ^
  --command bench\sim_robot_arm\simple_joint_move_001\command.json ^
  --log-dir logs
```

Generate a Markdown report from a log:

```bash
python -m cli.generate_report ^
  --log logs\exec_YYYYMMDD_HHMMSS_xxxxxxxx.json ^
  --output-dir output_reports ^
  --skip-plot
```

Omit `--skip-plot` to generate a PNG visualization when `matplotlib` is installed.

Run the full Stage 1 benchmark:

```bash
python -m cli.run_benchmark ^
  --bench bench\sim_robot_arm ^
  --log-dir logs\benchmark ^
  --output-json output_reports\stage1_benchmark_summary.json ^
  --output-md output_reports\stage1_benchmark_summary.md
```

Replay one execution log and compare the recomputed safety result:

```bash
python -m cli.replay_log ^
  --log logs\exec_YYYYMMDD_HHMMSS_xxxxxxxx.json
```

Run PyBullet backend smoke benchmark:

```bash
python -m cli.run_benchmark ^
  --backend pybullet ^
  --mode smoke ^
  --bench bench\sim_robot_arm
```

Compare mock and PyBullet backends:

```bash
python -m cli.compare_backends ^
  --bench bench\sim_robot_arm ^
  --backends mock pybullet ^
  --output-json output_reports\backend_comparison.json ^
  --output-md output_reports\backend_comparison.md
```

Generate PyBullet geometry diagnostics:

```bash
python -m cli.diagnose_backend_geometry ^
  --task bench\sim_robot_arm\mid_trajectory_collision_001 ^
  --output-json output_reports\mid_trajectory_geometry_diagnostics.json
```

Generate URDF-vs-mock calibration diagnostics:

```bash
python -m cli.calibrate_urdf_geometry ^
  --task bench\sim_robot_arm\mid_trajectory_collision_001 ^
  --output-json output_reports\mid_trajectory_urdf_calibration.json
```

Run the Stage 3 runtime MVP demo:

```bash
python -m cli.run_runtime_demo ^
  --task bench\sim_robot_arm\simple_joint_move_001 ^
  --backend mock ^
  --episode-dir output_reports\runtime_demo ^
  --json
```

## Architecture

```text
scene.json + command.json
  -> robot_safety.evaluate_joint_command
  -> SafetyResult
  -> gateway safety log
  -> Markdown report / optional 3D plot
  -> MockRealManAdapter simulated execution when approved

RobotObservation + RobotAction
  -> SafetyRuntime.step
  -> robot_safety.evaluate_joint_command_with_metadata
  -> conditional RobotDeviceAdapter.send_action
  -> RuntimeExecutionResult / blocked_reason
  -> EpisodeRecorder metadata + steps.jsonl
```

Execution logs include a schema version, input paths, review summary, trajectory summary, environment metadata, full scene/command payloads, safety result, and execution/adapter result.

Main modules:

```text
robot_safety/models.py        structured scene, command, and result models
robot_safety/trajectory.py    joint-space interpolation and delta metrics
robot_safety/kinematics.py    simplified deterministic 6-DOF FK
robot_safety/collision.py     link-sphere clearance and collision checks
robot_safety/safety_rules.py  rule-based decision logic
robot_safety/evaluator.py     safety gate orchestration
robot_safety/scorer.py        expected-contract scoring
robot_safety/benchmark.py     benchmark discovery, execution, and summaries
gateway/                      review and replayable execution logs
reports/                      Markdown and optional 3D visualization
robots/                       RobotAdapter and MockRealMan6DoFAdapter
sim/                          backend abstraction, mock backend, PyBullet backend, diagnostics
robot_runtime/                Stage 3 observation/action runtime and episode recorder
cli/                          runnable command-line entry points
```

## Benchmarks

Stage 1 includes eight simulation tasks:

```text
simple_joint_move_001          approve
joint_limit_violation_001      reject
obstacle_collision_001         reject
mid_trajectory_collision_001   reject, with nonzero worst-step collision
near_miss_clearance_001        manual_review
long_motion_delta_risk_001     manual_review
multi_obstacle_clearance_001   approve, with closest object/link reporting
invalid_command_001            reject, with structured invalid-command log
```

Each task contains:

```text
scene.json
command.json
expected.json
```

`expected.json` uses a structured contract with `expected_safety`, `expected_gateway`, `required_output_fields`, and a `clearance_assertion` mode. This keeps the benchmark tolerant of tiny FK numeric drift while still checking decision, risk, violations, critical obstacle attribution, and gateway execution behavior.

`obstacle_collision_001` validates fail-safe rejection when the initial posture is already in collision. `mid_trajectory_collision_001` validates the separate case where the interpolated trajectory hits an obstacle at a nonzero step.

## Roadmap

Near-term:

- backend-specific benchmark expectations
- visual replay for PyBullet diagnostics
- optional expected JSON schema file

Later:

- box/table obstacle support
- workspace and speed safety rules
- GUI replay / screenshot
- RealMan SDK adapter skeleton
- Agent-ready tools for reviewing candidate commands
- learning-based risk triage as advisory only, never as final safety authority

## Detailed Plan

The full Stage 1 planning document is kept in:

```text
docs/stage1_plan.md
```
