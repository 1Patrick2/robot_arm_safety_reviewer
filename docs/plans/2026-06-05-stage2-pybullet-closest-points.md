# Stage 2.5A PyBullet Closest-Point Collision Fidelity

## Purpose

Stage 2.5A improves the PyBullet backend collision fidelity. The current PyBullet backend uses `link_position_sphere_clearance`, which samples link-frame positions and compares those points with sphere obstacles. That is useful as a smoke backend, but it can miss collisions along the link body.

This stage upgrades the default PyBullet method to a PyBullet collision-geometry-based closest-point query over URDF collision geometry and sphere obstacle bodies.

## Scope

Included:

- create PyBullet static sphere collision bodies for `scene.obstacles`;
- replay each joint trajectory step with `resetJointState`;
- run `performCollisionDetection`;
- query robot link geometry against sphere obstacle bodies with `getClosestPoints`;
- compute `min_clearance`, `collision_free`, `closest_robot_link`, `closest_obstacle`, `worst_step`, and `violations`;
- record diagnostic metadata for collision method, fidelity, checked links, and closest-point search distance;
- keep the old `link_position_sphere_clearance` method as an internal fallback/comparison mode.

Excluded:

- GUI replay;
- dynamic simulation, motors, gravity, or `stepSimulation`;
- box/table obstacles;
- self-collision;
- RealMan SDK, ROS2, or MoveIt integration;
- Agent or LLM tool-use integration.

## Design

`PyBulletBackend` will support two internal methods:

```python
collision_method: Literal[
    "link_position_sphere_clearance",
    "pybullet_closest_points_sphere_collision",
]
```

The default becomes:

```text
pybullet_closest_points_sphere_collision
```

The previous method remains available for fallback and future comparison.

The closest-point method uses:

```text
DEFAULT_CLOSEST_POINT_DISTANCE = 0.30
```

This search distance is intentionally recorded in backend metadata because it affects which non-contact near pairs are returned.

The first implementation checks movable robot links by default and does not include the base link. This avoids base-obstacle false positives. The backend records `checked_links` in metadata so diagnostics can explain what was queried.

## Safety Semantics

Collision and clearance thresholds remain layered:

- `collision_free = False` only when the geometry query reports overlap/contact penetration with `contactDistance < 0`;
- positive but small `min_clearance` remains a clearance signal and is evaluated by the existing safety evaluator;
- hard clearance and manual-review thresholds should not be merged into the PyBullet collision test.

This preserves the existing distinction between physical overlap and low-clearance risk.

## Tests

Add focused Stage 2.5A tests:

- default PyBullet metadata reports `pybullet_closest_points_sphere_collision`;
- `simple_joint_move_001` remains clear;
- `obstacle_collision_001` produces geometric collision with `environment_collision`;
- `mid_trajectory_collision_001` produces meaningful closest-point diagnostics without requiring a hard-coded final decision;
- fallback method can still be selected and reports `link_position_sphere_clearance`.

Update existing metadata tests and any base-link collision test to account for the default link filtering.

## Verification

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp/current
```

Run PyBullet smoke benchmark:

```powershell
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.run_benchmark --backend pybullet --mode smoke
```

Run mock scored benchmark:

```powershell
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.run_benchmark --backend mock
```

Run backend comparison:

```powershell
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.compare_backends --bench bench\sim_robot_arm --backends mock pybullet --output-json output_reports\backend_comparison.json --output-md output_reports\backend_comparison.md
```

Then update `docs/stage2_backend_diagnostics.md` with before/after comparison:

```text
Before Stage 2.5A:
Decision matches: 6/8
Risk matches: 7/8

After Stage 2.5A:
Decision matches: ?/8
Risk matches: ?/8
```
