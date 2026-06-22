# Robot Action Safety Sandbox

[Chinese README](README.zh-CN.md)

Robot Action Safety Sandbox is a deterministic robot action safety evaluation and diagnostic evidence framework.

It evaluates robot action sequences, records safety evidence, validates expected-vs-actual contracts, and provides optional diagnostic analysis output.

The next major direction is perception-aware safety fusion, where structured perception results can be converted into safety constraints and combined with robot trajectory evidence.

**It is not primarily an Agent project.**
**LLM / diagnostic analysis is optional and diagnostic-only.**
**Safety decisions are made by the deterministic safety runtime.**
**LLM / diagnostic analysis output must not approve, reject, modify, or execute robot actions.**

The project started as `RobotArmSafetyReviewer`. It is still a safety reviewer, not a motion planner. It must not silently modify trajectories, generate obstacle-avoiding paths, or let an LLM decide robot safety.

## Current Status

Current stage: **Stage 5.3-A: Perception-Aware Regression Fixtures — complete**. R1-C diagnostics migration is under validation.
Next major stage: **Perception Model Adapter Protocol (Stage 5.4-A)** once R1-C passes.

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
- Stage 3.9: diagnostic runtime integration guardrails and trace.
- Stage 3.10: evidence manifest for diagnostic outputs.
- Stage 3.11: diagnostic regression for batch verification.
- Stage 3.12: demo flow documentation and project hardening.
- Stage 4.2A: expected contract scaffold (`load_expected_contract`, `build_actual_summary`, `validate_expected_contract`).
- Stage 4.2B: Level-2 safety scenarios with expected contracts.
- Stage 4.2C: regression `--case-set` CLI (`smoke` / `level2` / `all`).
- Stage 4.3A: `evidence_groups` in `evidence_manifest.json` (runtime, safety, geometry, visual, structured_visual, diagnostic, agent).
- Stage 4.3B: `required_evidence_groups` in `expected_contract.v1`.
- Stage 4.3C: `required_actual_fields`, `expected_closest_obstacle`, `min_clearance_lte` / `min_clearance_gte`.
- Stage 4.4A: Diagnostic analysis schema and deterministic fake analyst.
- Stage 4.4A-polish: evidence_refs consistency cleanup for fake diagnostic analysis.
- Stage 4.4B: diagnostic analysis application service and `diagnostic analyze` CLI.
- Stage 5.1: perception result schema (`perception_result.v1`), loader, fake perception adapter.
- Stage 5.1-polish: unknown safe zone and distance threshold cleanup.
- Stage 5.2: perception safety fusion (`PerceptionSafetyFusionResult`).
- Stage 5.2-polish: fusion edge-case coverage.
- Stage 5.3A: perception-aware regression fixtures and focused tests.

## Safety Boundary

- Safety decisions are deterministic: `approve`, `manual_review`, or `reject`.
- Only `approve` reaches `RobotDeviceAdapter.send_action()`.
- `manual_review` and `reject` are blocked and recorded.
- Agent context and diagnostic analysis output are diagnostic evidence only. They must not approve, reject, modify, or execute robot actions.
- The mock backend and PyBullet backend are diagnostic simulation tools, not certified hardware validation.

Deferred:

- RealMan SDK / hardware execution.
- ROS2 / MoveIt.
- VLA or autonomous robot-control agent.
- Large remote dataset integration.
- Real edge deployment, ONNX, RKNN, or camera integration.

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
trajectory_overview_data.json
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

### Diagnostic Regression with Case Sets

The `diagnostic regression` command supports three case sets via `--case-set`:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic regression --case-set smoke --json
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic regression --case-set level2 --json
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic regression --case-set all --json
```

Case set contents:

| Set | Cases |
|---|---|
| `smoke` (default) | `simple_safe_sequence` — pipeline smoke test |
| `level2` | 3 Level-2 scenarios with expected contracts |
| `all` | smoke + level2 |

Level-2 scenarios:

- **near_threshold_clearance_sequence**: near-threshold clearance, manual_review expected.
- **midpoint_collision_sequence**: trajectory-level collision, reject expected.
- **mixed_decision_sequence**: approve + manual_review + reject in one sequence.

Each level2 case validates `pipeline_passed`, `evidence_complete`, `contract_passed`, required evidence groups, required actual fields, closest obstacle match, and min_clearance thresholds in the regression summary.

### Run Diagnostic Pipeline from an Episode

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic run ^
  --episode-id <episode_id> ^
  --db output_reports\runtime_metrics\runtime_metrics.db ^
  --output-dir output_reports\diagnostics ^
  --json
```

### Generate Report from Existing Context

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic report ^
  --context output_reports\diagnostics\<episode_id>\context\diagnostic_context.json ^
  --output-dir output_reports\diagnostic_report ^
  --json
```

### Analyze Existing Diagnostic Evidence

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic analyze ^
  --context output_reports\diagnostics\<episode_id>\context\diagnostic_context.json ^
  --manifest output_reports\diagnostics\<episode_id>\evidence_manifest.json ^
  --report output_reports\diagnostics\<episode_id>\diagnostic_report.md ^
  --output-dir output_reports\diagnostic_analysis ^
  --provider fake ^
  --json
```

This command produces `llm_diagnostic_analysis.json` using the deterministic fake analyst. It does not affect safety decisions.

## Output Artifacts

Each stage produces specific evidence files:

| Stage | Files |
|---|---|
| Episode recording | `metadata.json`, `steps.jsonl`, `episode_summary.md` |
| Visual sandbox | `clearance_curve.png`, `trajectory_overview.png`, `trajectory_overview_data.json` |
| Runtime metrics DB | `runtime_metrics.db` (SQLite — `runs`, `steps`, `artifacts` tables) |
| Diagnostic context | `diagnostic_context.json`, `diagnostic_context.md` |
| Diagnostic runtime | `diagnostic_report.md`, `diagnostic_runtime_trace.json` |
| Diagnostic agent (optional) | `diagnostic_agent_report.md` |
| Evidence manifest | `evidence_manifest.json` — unified evidence index for one diagnostic run. Records all artifacts, existence checks, and summary metrics. |
| Regression summary | `regression_summary.json` — aggregate results across multiple regression cases. |
| Diagnostic analysis | `llm_diagnostic_analysis.json` — optional structured diagnostic analysis generated from existing evidence. |

## What This Project Is Not

```text
This project is NOT:
- an LLM-controlled robot executor
- a motion planner replacement
- a RAG chatbot
- a VLA training system
- a robot control agent
- a generic Agent framework
- an Edge AI deployment demo yet

It IS:
- a safety evaluation and diagnostic evidence framework for robot action sequences
```

It can later integrate perception models or edge inference, but the current project does not require real edge deployment.

## Architecture

```text
PolicyActionSequence / dataset sample
  -> sandbox run
  -> deterministic SafetyRuntime review
  -> EpisodeRecorder
  -> visual artifacts
  -> runtime metrics DB
  -> diagnostic context
  -> deterministic diagnostic report
  -> evidence_manifest.json
  -> expected-vs-actual contract validation
  -> diagnostic regression summary
  -> optional diagnostic analysis
```

Planned future direction:

```text
Planned Stage 5: Perception-Aware Safety Fusion
  -> perception_result.json
  -> perception-to-safety constraints
  -> trajectory + perception risk fusion
  -> perception-aware regression cases
```

Main modules:

```text
robot_safety/                 deterministic safety models, trajectory, collision, evaluator, scorer
sim/                          backend abstraction, mock backend, PyBullet backend, diagnostics
robot_runtime/                runtime actions, observations, devices, sequences, episode recorder/loader
dataset_adapters/             mini_sequence and local LeRobot-style adapters
runtime_db/                   SQLite schema, repository, and episode ingest
diagnostic_runtime/           diagnostic runtime framework
  context/                      deterministic diagnostic context package
  tools/                        read-only diagnostic context query layer
  report/                       deterministic diagnostic report generation
  agent/                        fake / DeepSeek diagnostic agent runner
  guardrails/                   post-generation safety boundary checker
  runtime/                      orchestration and trace for diagnostic workflow
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
