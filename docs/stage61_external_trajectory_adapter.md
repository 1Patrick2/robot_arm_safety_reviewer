# Stage 6.1: External Trajectory Adapter

## Motivation

v0.1 action inputs are mostly hand-authored benchmark JSON files.
v0.2 proves the framework can ingest real-world robot demonstration
trajectories, normalize them into the internal `PolicyActionSequence`
schema, and run them through the same safety and evidence pipeline.

## Supported Sources

| Source | Status | Default |
|---|---|---|
| LeRobot-style local JSON | ✅ Implemented | Always available |
| LeRobot Hugging Face Hub | ✅ Optional (manual-only) | Requires `pip install lerobot` |
| robomimic / DROID / Open X | 🔜 Future | Not planned for v0.2 |

## Data Flow

```
lerobot_style_episode.json  (or LeRobot Hub dataset)
  → load_lerobot_style_episode()  /  load_lerobot_hub_episode()
    → ExternalTrajectory
      → external_trajectory_to_policy_sequence()
        → PolicyActionSequence
          → SafetyRuntime evaluation
            → DiagnosticContext
              → EvidenceManifest (external_trajectory group)
                → ExpectedContract validation
```

## Mapping Limitations (Stage 6.1)

| Constraint | Value |
|---|---|
| Source action type | `joint_position` only |
| Target command type | `joint_space` only |
| Joint count | Configurable (default 6) |
| Scale/offset | Applied linearly per joint |
| Current joints policy | `zeros` or `previous_target` |

## External Trajectory Evidence

When an `external_trajectory_record.json` is provided to
`build_evidence_manifest()`, the manifest gains:

- **artifact**: `external_trajectory_record`
- **checks**: `has_external_trajectory_evidence`, `external_trajectory_record_valid`
- **summary fields**: `external_dataset_name`, `external_episode_id`,
  `external_robot_name`, `external_action_type`, `external_frame_count`,
  `external_sequence_id`
- **evidence group**: `external_trajectory` with `available=True`

## Safety Boundary

- External actions are evaluated inside the project's own robot scene/model.
- The project does **not** claim hardware-level safety certification
  for the original external dataset robot.
- The project claims: *external demonstration trajectories can be
  normalized into the internal action schema and evaluated in the
  project's deterministic safety pipeline*.

## Optional LeRobot Hub Smoke

```powershell
$env:RUN_LEROBOT_HUB_SMOKE="1"
$env:LEROBOT_REPO_ID="lerobot/aloha_mobile_cabinet"
$env:LEROBOT_EPISODE_INDEX="0"
python -m pytest tests/manual/test_lerobot_hub_smoke.py -q
```

Requires: `pip install lerobot`

## Validation Commands

```powershell
# Core trajectory tests
python -m pytest tests/test_stage61_external_trajectory_schema.py tests/test_stage61_lerobot_style_adapter.py tests/test_stage61_external_trajectory_mapping.py tests/test_stage61_external_trajectory_evidence.py -q

# Evidence + manifest + contract
python -m pytest tests/test_evidence_manifest.py tests/test_stage42_diagnostic_contracts.py -q

# Existing perception pipeline (no regression)
python -m pytest tests/test_stage54b_perception_inference_evidence.py tests/test_stage54c_ultralytics_yolo_adapter_contract.py -q
```

## Directory Layout

```
bench/
  adapters/
    external_trajectory.py           ExternalTrajectory, ActionMappingConfig, conversion
    lerobot_episode_adapter.py        Local LeRobot-style JSON loader
    optional_lerobot_hub_adapter.py   Hub loader (manual-only, requires lerobot)
  external_trajectory_smoke/          Smoke fixture
    lerobot_style_episode.json
    mapping_config.json
    scene.json
    expected_contract.json
diagnostics/evidence/
  external_trajectory.py              ExternalTrajectoryRecord + writer
tests/
  test_stage61_external_trajectory_schema.py
  test_stage61_lerobot_style_adapter.py
  test_stage61_external_trajectory_mapping.py
  test_stage61_external_trajectory_evidence.py
  manual/test_lerobot_hub_smoke.py
```
