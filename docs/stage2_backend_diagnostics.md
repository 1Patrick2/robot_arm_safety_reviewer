# Stage 2 Backend Diagnostics

[中文版](stage2_backend_diagnostics.zh-CN.md)

## Purpose

This document records backend comparison diagnostics between the deterministic mock backend and the PyBullet backend. The goal is not to prove that both backends match exactly. The goal is to make backend differences visible enough to decide the next engineering step.

## Current Backends

### Mock Backend

- Name: `mock`
- Collision method: `segment_sphere_clearance`
- Model version: `mock_geometry_v1`
- Role: deterministic baseline for regression tests, benchmark scoring, and fallback execution.

### PyBullet Backend

- Name: `pybullet`
- Mode: `DIRECT`
- URDF: `assets/robots/mock_realman_6dof/robot.urdf`
- Collision method: `pybullet_closest_points_sphere_collision`
- Fidelity: `collision_geometry`
- Closest-point search distance: `0.30`
- Base collision checking: disabled by default
- Boundary: uses PyBullet closest-point queries over URDF collision geometry and sphere obstacle bodies. It is higher fidelity than link-frame sampling, but still depends on the URDF collision geometry and benchmark obstacle modeling.

## Before Stage 2.5A

The Stage 2.4 PyBullet backend used `link_position_sphere_clearance`. Earlier notes reported `Decision matches: 6/8`, but that value used the old strict-style match definition. Reinterpreted with the current metric names:

| Metric | Value |
|---|---:|
| Tasks | 8 |
| Decision matches | 7 |
| Risk matches | 7 |
| Clearance band matches | 6 |
| Attribution matches | 8 |
| Strict matches | 6 |
| Backend errors | 0 |

Main disagreement:

| Task | Mock | PyBullet | Diagnosis |
|---|---|---|---|
| `mid_trajectory_collision_001` | `reject`, high, min clearance `-0.064573` | `manual_review`, medium, min clearance `0.089615` | `decision_disagreement` |

Likely cause: link-frame position sampling could miss an overlap along the link body.

## After Stage 2.5A

Generated from:

```powershell
python -m cli.compare_backends `
  --bench bench\sim_robot_arm `
  --backends mock pybullet `
  --output-json output_reports\backend_comparison.json `
  --output-md output_reports\backend_comparison.md
```

| Metric | Value |
|---|---:|
| Tasks | 8 |
| Decision matches | 8 |
| Risk matches | 8 |
| Clearance band matches | 6 |
| Attribution matches | 7 |
| Strict matches | 6 |
| Backend errors | 0 |

The PyBullet backend now reports:

```json
{
  "collision_method": "pybullet_closest_points_sphere_collision",
  "fidelity": "collision_geometry",
  "closest_point_search_distance": 0.3,
  "include_base_collision": false
}
```

## Consistent Cases

| Task | Decision | Diagnosis |
|---|---|---|
| `invalid_command_001` | `reject` | `consistent_reject` |
| `joint_limit_violation_001` | `reject` | `consistent_reject` |
| `long_motion_delta_risk_001` | `manual_review` | `consistent_manual_review` |
| `near_miss_clearance_001` | `manual_review` | `consistent_manual_review` |
| `obstacle_collision_001` | `reject` | `consistent_reject` |
| `simple_joint_move_001` | `approve` | `consistent_safe` |

These cases show that the backend abstraction, logging, reporting, and benchmark comparison pipeline remain stable after the closest-point upgrade.

## Remaining Differences

### `mid_trajectory_collision_001`

| Backend | Decision | Risk | Min Clearance | Closest Link | Closest Obstacle | Worst Step | Violations |
|---|---|---|---:|---|---|---:|---|
| `mock` | `reject` | `high` | -0.064573 | `link_4` | `sphere_mid` | 10 | `environment_collision` |
| `pybullet` | `reject` | `high` | 0.045865 | `link_3` | `sphere_mid` | 5 | `clearance_violation` |

Diagnosis: `clearance_threshold_disagreement`

Stage 2.5A improved this case from a decision/risk mismatch to a consistent high-risk rejection. The remaining difference is geometric: the mock model reports penetration on `link_4`, while PyBullet reports a positive but hard-threshold clearance on `link_3`.

Engineering implication: the safety decision is now aligned, but geometry attribution and exact clearance remain uncalibrated between mock segment geometry and URDF collision geometry.

### `multi_obstacle_clearance_001`

| Backend | Decision | Risk | Min Clearance | Closest Link | Closest Obstacle | Worst Step | Diagnosis |
|---|---|---|---:|---|---|---:|---|
| `mock` | `approve` | `low` | 0.095 | `link_3` | `sphere_near` | 0 | baseline |
| `pybullet` | `approve` | `low` | 0.100 | `link_3` | `sphere_near` | 4 | `clearance_threshold_disagreement` |

Both backends approve the command with low risk. The remaining mismatch is a threshold-band artifact around the manual-review boundary.

Engineering implication: this does not block PyBullet use as a diagnostic backend. It confirms that exact clearance values should not be treated as calibrated across backends yet.

## Stage 2.5A Conclusion

Stage 2.5A completed the intended backend fidelity upgrade:

- PyBullet now uses URDF collision geometry closest-point checking by default;
- the previous link-position sampling method remains available internally;
- metadata records the collision method, fidelity, checked links, and search distance;
- PyBullet smoke benchmark completes all 8 tasks;
- mock benchmark still passes all 8 tasks;
- backend comparison has 0 backend errors;
- final decision matches improved from 7/8 to 8/8;
- risk matches improved from 7/8 to 8/8.

Strict matches remain 6/8 because clearance-band and attribution differences remain on `mid_trajectory_collision_001` and `multi_obstacle_clearance_001`.

## Stage 2.5B Geometry Diagnostics

Stage 2.5B added structured geometry diagnostics for PyBullet tasks:

```powershell
python -m cli.diagnose_backend_geometry `
  --task bench\sim_robot_arm\mid_trajectory_collision_001 `
  --output-json output_reports\mid_trajectory_geometry_diagnostics.json
```

The diagnostic output records:

- checked links;
- per-step joint values;
- per-step PyBullet link poses;
- closest-point observations;
- the worst robot-link / obstacle pair.

For `mid_trajectory_collision_001`, the diagnostic worst pair is:

| Field | Value |
|---|---|
| Step | 5 |
| Robot link | `link_3` |
| Obstacle | `sphere_mid` |
| Clearance | 0.045865 |
| Position on robot | `[0.585978, 0.078356, 0.167939]` |
| Position on obstacle | `[0.583853, 0.099532, 0.208567]` |
| Normal on obstacle | `[0.046325, -0.461707, -0.885822]` |

Checked links:

```text
link_1, link_2, link_3, link_4, link_5, link_6
```

At the worst step, PyBullet reports these relevant link poses:

| Link | Position | Orientation |
|---|---|---|
| `link_3` | `[0.456111, 0.045764, 0.148053]` | `[0.0, 0.0, 0.049979, 0.99875]` |
| `link_4` | `[0.694912, 0.069724, 0.148053]` | `[0.0, 0.0, 0.049979, 0.99875]` |

For `multi_obstacle_clearance_001`, the diagnostic worst pair is:

| Field | Value |
|---|---|
| Step | 0 |
| Robot link | `link_3` |
| Obstacle | `sphere_near` |
| Clearance | 0.100 |

Interpretation:

- Stage 2.5B confirms the PyBullet closest-point path is producing structured, inspectable geometry data.
- The `mid_trajectory_collision_001` difference is no longer a backend execution or missing-closest-point problem. PyBullet sees the closest geometry on `link_3` with hard-threshold clearance, while the mock segment model reports penetration on `link_4`.
- The `multi_obstacle_clearance_001` difference remains a threshold-boundary issue around `0.10`.

## Stage 2.5C URDF Calibration

Stage 2.5C added a URDF-vs-mock calibration report:

```powershell
python -m cli.calibrate_urdf_geometry `
  --task bench\sim_robot_arm\mid_trajectory_collision_001 `
  --output-json output_reports\mid_trajectory_urdf_calibration.json
```

For `mid_trajectory_collision_001`, the calibration summary is:

| Field | Value |
|---|---|
| PyBullet worst step | 5 |
| PyBullet closest | `link_3`, `sphere_mid`, clearance `0.045865` |
| Mock at PyBullet worst step | `link_3`, `sphere_mid`, clearance `0.002415` |
| Mock overall worst | step `10`, `link_4`, `sphere_mid`, clearance `-0.064573` |
| Conclusion | `kinematic_model_mismatch` |

Relevant link calibration:

| Link | URDF Length | Mock Length | Length Delta | Endpoint Alignment Error |
|---|---:|---:|---:|---:|
| `link_3` | 0.28 | 0.28 | 0.0 | 0.153891 |
| `link_4` | 0.20 | 0.20 | 0.0 | 0.118669 |

Interpretation:

- URDF collision lengths for `link_3` and `link_4` match the mock link lengths.
- The remaining difference is not a simple collision-size mismatch.
- At PyBullet's worst step, both models identify `link_3` as closest to `sphere_mid`, but mock clearance is much tighter.
- Across the full trajectory, the mock backend's overall worst case occurs later at step 10 on `link_4`.
- This points to a kinematic-model mismatch: the mock FK uses simplified yaw/pitch updates for later joints, while the URDF has explicit joint axes and x-axis wrist rotations.

## Stage 2.5 Conclusion

Stage 2.5 is complete for the current project scope:

- Stage 2.5A upgraded PyBullet from link-frame sampling to collision-geometry closest-point checking.
- Stage 2.5B added inspectable PyBullet geometry diagnostics.
- Stage 2.5C added URDF-vs-mock calibration reporting.
- The remaining differences are explainable as mock-vs-URDF model differences, not backend runtime failures.

Recommended next path:

```text
Stage 2.6: Backend-specific expectations and/or visual replay
```

Recommended priority:

1. Add backend-specific benchmark expectations if PyBullet scoring should be measured independently from mock scoring.
2. Add visual replay after expectations are clear, so screenshots demonstrate known backend behavior instead of unresolved calibration ambiguity.
