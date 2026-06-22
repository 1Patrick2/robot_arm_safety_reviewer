# Core Function Map

This document is a quick code-reading map for RobotArmSafetyReviewer. It lists the main files, the functions or classes worth reading first, and the role each one plays in the safety-review workflow.

Stage R1 is migrating stage-grown modules into stable domain packages. `robot/safety/` is the canonical implementation path for robot safety core code. `robot_safety/` is only a compatibility shim and should not receive new implementation code.

`robot/safety/benchmark.py` and `robot/safety/scorer.py` are transitional utilities retained from the former `robot_safety` package. Future benchmark orchestration should stay outside low-level safety core.

| Layer | File | Core Function / Class | Purpose |
|---|---|---|---|
| Data model | `robot/safety/models.py` | `Scene`, `JointCommand`, `SafetyResult`, `Violation` | Defines the structured input/output contract used across CLI, gateway, evaluator, benchmark, and reports. |
| Trajectory | `robot/safety/trajectory.py` | `interpolate_joint_trajectory` | Converts `current_joints -> target_joints` into an interpolated joint-space trajectory for whole-path checking. |
| Trajectory | `robot/safety/trajectory.py` | `compute_max_joint_delta` | Measures large motion delta risk for manual-review decisions. |
| Mock FK | `robot/safety/kinematics.py` | `forward_kinematics_6dof` | Builds simplified mock robot link points for deterministic segment-based collision checking. |
| Mock collision | `robot/safety/collision.py` | `check_trajectory_collision` | Checks link-sphere collision and clearance along the interpolated trajectory. |
| Safety rules | `robot/safety/safety_rules.py` | `check_trajectory_joint_limits` | Validates every interpolated joint state against configured joint limits. |
| Safety rules | `robot/safety/safety_rules.py` | `classify_risk_level`, `make_decision` | Converts geometry and rule signals into `low/medium/high` and `approve/manual_review/reject`. |
| Evaluator | `robot/safety/evaluator.py` | `evaluate_joint_command` | Backward-compatible review entry point returning only `SafetyResult`. |
| Evaluator | `robot/safety/evaluator.py` | `evaluate_joint_command_with_metadata` | Explicit review entry point returning `SafetyResult` plus backend metadata. |
| Legacy robot safety shim | `robot_safety/*.py` | module re-exports | Compatibility shims that re-export `robot.safety.*` while existing imports migrate. |
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
| Policy action | `robot_runtime/policy_action.py` | `PolicyAction`, `policy_action_to_robot_action` | Defines policy-proposed action inputs and converts `joint_target` / `delta_joint` actions into runtime `RobotAction` objects. |
| Policy sequence | `robot_runtime/action_sequence.py` | `PolicyActionSequence` | Loads and serializes local action-sequence fixtures for future sequence runtime and dataset adapters. |
| Application runtime | `application/runtime_service.py` | `RuntimeTaskRequest`, `run_runtime_task` | Reusable service for assembling action source, scene provider, backend, robot device, recorder, and runtime step execution. |
| Application review | `application/review_service.py` | `ReviewCommandRequest`, `review_command` | Reusable service wrapper around review-only safety-gate execution. |
| Application core | `application/core.py` | `AppContext`, `ArtifactRef`, `AppResult` | Common result, artifact, and run-context envelope for future service, CLI, batch, and agent-tool outputs. |
| Dataset adapter protocol | `dataset_adapters/base.py` | `DatasetAdapter` | Protocol for `list_sequences()` and `load_sequence()`. |
| Mini sequence adapter | `dataset_adapters/mini_sequence_adapter.py` | `MiniSequenceAdapter` | Reads local `samples/policy_sequences/*.json` files and returns `PolicyActionSequence` objects. |
| LeRobot-style adapter | `dataset_adapters/lerobot_style_adapter.py` | `LeRobotStyleAdapter` | Reads local `samples/lerobot_style/episodes/*.json` files with LeRobot-style episode layout. |
| Dataset service | `application/dataset_service.py` | `DatasetListRequest`, `DatasetExportSequenceRequest`, `dataset_list`, `dataset_export_sequence` | Reusable application service wrapping adapter operations for CLI and future entry points. |
| Metrics DB schema | `runtime_db/schema.py` | `init_runtime_db` | Creates SQLite tables (runs, steps, artifacts, schema_meta). |
| Metrics repository | `runtime_db/repository.py` | `RuntimeMetricsRepository` | Parameterised-SQL read/write for run and step records. |
| Episode ingest | `runtime_db/episode_ingest.py` | `ingest_episode`, `build_run_record`, `build_step_records`, `build_artifact_records` | Extracts structured metrics from an episode directory and writes to DB. |
| Metrics service | `application/metrics_service.py` | `metrics_ingest_episode`, `metrics_list_runs`, `metrics_show_run` | Application service wrapping runtime_db operations for CLI and agents. |
| Diagnostic context model | `diagnostic_runtime/context/models.py` | `AgentContext`, `AgentContextStep`, `AgentContextArtifact` | Defines deterministic diagnostic context data for review tools. |
| Diagnostic context builder | `diagnostic_runtime/context/builder.py` | `build_agent_context_from_db` | Builds a diagnostic context package from runtime metrics DB records. |
| Diagnostic context renderer | `diagnostic_runtime/context/render.py` | `write_agent_context_files` | Writes `diagnostic_context.json` and `diagnostic_context.md`. |
| Diagnostic context service | `application/agent_context_service.py` | `build_agent_context` | Application service wrapping context generation for CLI and future diagnostic tools. |
| Diagnostic service | `application/diagnostic_service.py` | `run_diagnostic` | Full diagnostic pipeline: build context → runtime → report → optional agent → manifest. |
| Diagnostic service | `application/diagnostic_service.py` | `run_diagnostic_report` | Report-only path from existing context (reuses diagnostic runtime). |
| Diagnostic service | `application/diagnostic_service.py` | `run_diagnostic_regression` | Batch pipeline over fixed cases: sandbox → metrics → diagnostic → manifest → summary. Supports `--case-set {smoke,level2,all}`. |
| Diagnostic analysis service | `application/diagnostic_analysis_service.py` | `run_diagnostic_analysis` | Loads diagnostic context + evidence manifest + optional report, runs fake diagnostic analyst, writes `llm_diagnostic_analysis.json`. |
| Expected contract | `application/diagnostic_contracts.py` | `ExpectedContract` | Data class for loading `expected_contract.v1` files. |
| Expected contract | `application/diagnostic_contracts.py` | `load_expected_contract` | Loads and validates an `expected_contract.v1` JSON file. |
| Expected contract | `application/diagnostic_contracts.py` | `build_actual_summary` | Extracts actual safety-outcome summary (total_steps, approved, rejected, final_status, etc.) from a diagnostic context dict. |
| Expected contract | `application/diagnostic_contracts.py` | `validate_expected_contract` | Compares actual outcomes against expected_contract.v1, including step counts, final status, required artifacts, required evidence groups, required actual fields, closest obstacle, and min_clearance thresholds. |
| Evidence manifest | `reports/evidence_manifest.py` | `build_evidence_manifest` | Builds `evidence_manifest.json` — unified evidence index with artifact existence checks. Now emits `evidence_groups` for runtime/safety/geometry/visual/structured_visual/diagnostic/agent. |
| Evidence manifest | `reports/evidence_manifest.py` | `write_evidence_manifest` | Writes manifest dict to JSON file. |
| CLI diagnostic commands | `cli/commands/diagnostic.py` | `register_diagnostic_commands` | Registers `diagnostic run`, `diagnostic report`, `diagnostic regression` with `--case-set {smoke,level2,all}`, and `diagnostic analyze`. |
| CLI diagnostic analyze | `cli/commands/diagnostic.py` | `diagnostic analyze` | Runs optional diagnostic analysis from existing context and manifest. |
| Level-2 scenarios | `bench/level2_safety_scenarios/` | `scene.json`, `sequence.json`, `expected_contract.json` per case | Level-2 safety scenario fixtures for Stage 4.2 regression with expected contracts. |
| Diagnostics tools | `diagnostic_runtime/tools/context_tools.py` | `load_diagnostic_context`, `get_episode_summary`, `list_critical_steps`, `get_worst_step`, `get_artifact_index` | Read-only query layer over diagnostic_context.json. |
| Diagnostics report | `diagnostic_runtime/report/deterministic.py` | `build_diagnostic_report` | Generates deterministic diagnostic_report.md from context. |
| Diagnostic analysis models | `diagnostic_runtime/analysis/models.py` | `DiagnosticAnalysis` / `RootCauseHypothesis` | Structured diagnostic analysis schema. |
| Fake diagnostic analyst | `diagnostic_runtime/analysis/fake_analyst.py` | `run_fake_diagnostic_analyst` | Deterministic evidence-based diagnostic analysis; no external LLM call. |
| Evidence refs | `diagnostic_runtime/analysis/evidence_refs.py` | `build_basic_evidence_refs` | Builds evidence reference paths from summary fields and available evidence groups. |
| Diagnostic agent runner | `diagnostic_runtime/agent/runner.py` | `run_diagnostic_agent` | Runs a diagnostic-only agent with strict safety boundaries. |
| Diagnostic agent fake | `diagnostic_runtime/agent/adapters/fake.py` | `run_fake_agent` | Deterministic fake agent for testing without an LLM. |
| DeepSeek adapter | `diagnostic_runtime/agent/adapters/deepseek.py` | `run_deepseek_agent` | Provider adapter for DeepSeek API diagnostic smoke tests. |
| Safety guardrail | `diagnostic_runtime/guardrails/safety_check.py` | `check_agent_report`, `check_agent_report_or_raise` | Post-generation safety boundary check for agent output. |
| Runtime runner | `diagnostic_runtime/runtime/runner.py` | `run_diagnostic_runtime` | Unified orchestration of diagnostic workflow with trace output. |
| CLI output | `cli/output.py` | `print_json`, result-specific print helpers | Shared formatting helpers that keep CLI command modules from duplicating JSON and text output logic. |
| Benchmark | `robot/safety/benchmark.py` | `run_benchmark` | Discovers benchmark tasks, runs reviews, writes logs, and builds summaries. |
| Scorer | `robot/safety/scorer.py` | `score_execution_log` | Compares actual logs with expected task contracts. |
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
| Unified CLI | `cli/main.py` | `main` | Stage 3.1 unified entry point backed by application services. |
| Unified CLI command | `cli/commands/runtime.py` | `register_runtime_commands` | Registers `python -m cli.main runtime run`. |
| Unified CLI command | `cli/commands/review.py` | `register_review_commands` | Registers `python -m cli.main review`. |
| Unified CLI command | `cli/commands/sequence.py` | `register_sequence_commands` | Registers `python -m cli.main sequence run`. |
| Unified CLI command | `cli/commands/dataset.py` | `register_dataset_commands` | Registers `python -m cli.main dataset list` and `python -m cli.main dataset export-sequence`. |
| Unified CLI command | `cli/commands/metrics.py` | `register_metrics_commands` | Registers `python -m cli.main metrics ingest`, `list-runs`, and `show-run`. |
| Unified CLI command | `cli/commands/context.py` | `register_context_commands` | Registers `python -m cli.main context build`. |

Boundary rules:

- CLI modules call application services and `cli.output`.
- `application` may orchestrate `robot`, `robot_runtime`, `sim`, `gateway`, `reports`, `runtime_db`, `diagnostic_runtime/context`, and `dataset_adapters`.
- `robot`, `robot_runtime`, `sim`, `gateway`, `runtime_db`, `diagnostic_runtime`, and `dataset_adapters` must not import `application`, `agent`, or `robot_tools`.
- Future diagnostic agents should call tool wrappers that call application services; agents must not call robot device execution methods directly.

Suggested reading order:

1. `robot/safety/models.py`
2. `robot/safety/evaluator.py`
3. `sim/base.py`, `sim/mock_backend.py`, `sim/pybullet_backend.py`
4. `gateway/safety_gate.py`, `gateway/execution_logger.py`
5. `robot/safety/benchmark.py`, `robot/safety/scorer.py`
6. `reports/backend_comparison.py`
7. `sim/pybullet_diagnostics.py`, `sim/urdf_calibration.py`
8. `robot_runtime/types.py`, `robot_runtime/safety_runtime.py`, `robot_runtime/episode_recorder.py`
9. `robot_runtime/policy_action.py`, `robot_runtime/action_sequence.py`
10. `application/core.py`, `application/runtime_service.py`, `application/review_service.py`, `application/sequence_runtime_service.py`, `application/dataset_service.py`, `cli/output.py`, `cli/main.py`
11. `dataset_adapters/base.py`, `dataset_adapters/mini_sequence_adapter.py`
12. `runtime_db/schema.py`, `runtime_db/repository.py`, `runtime_db/episode_ingest.py`
13. `application/metrics_service.py`, `application/sandbox_service.py`
14. `diagnostic_runtime/context/models.py`, `diagnostic_runtime/context/builder.py`, `diagnostic_runtime/context/render.py`
15. `diagnostic_runtime/tools/context_tools.py`, `diagnostic_runtime/report/deterministic.py`
16. `diagnostic_runtime/agent/runner.py`, `diagnostic_runtime/agent/adapters/fake.py`
17. `diagnostic_runtime/guardrails/safety_check.py`, `diagnostic_runtime/runtime/runner.py`
