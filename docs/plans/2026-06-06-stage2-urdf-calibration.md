# Stage 2.5C URDF Collision Geometry Calibration

## Goal

Complete Stage 2.5 by explaining the remaining mock-vs-PyBullet geometry differences with a structured calibration report.

## Design

Stage 2.5A upgraded PyBullet to closest-point collision queries. Stage 2.5B added per-step PyBullet geometry diagnostics. Stage 2.5C compares those diagnostics with the mock forward-kinematics segment model.

The calibration report should not change the safety review path. It should answer:

- which mock link segment is closest to the benchmark obstacle;
- which PyBullet collision link is closest to the same obstacle;
- how far mock segment endpoints are from PyBullet collision-axis endpoints;
- whether remaining differences look like URDF size/origin issues or mock-vs-URDF kinematic-model differences.

## Approach

Add `sim/urdf_calibration.py`:

- parse URDF box collision origins and sizes for `link_1` through `link_6`;
- reuse `diagnose_task_geometry()` to get PyBullet worst step and link poses;
- compute mock FK points at the same worst step;
- derive mock link segments from adjacent FK points;
- derive PyBullet collision-axis endpoints from link pose + URDF collision box origin/size;
- compute endpoint deltas and length deltas;
- identify the closest mock segment to the same obstacle;
- return JSON-serializable calibration data and a compact conclusion.

Add `cli/calibrate_urdf_geometry.py`:

- accepts `--task`;
- optionally writes `--output-json`;
- prints a short summary with mock closest link, PyBullet closest link, clearance values, and conclusion.

## Expected Finding

The likely finding for `mid_trajectory_collision_001` is not a simple URDF size mismatch. The URDF link sizes match the configured link lengths, but mock FK uses a simplified wrist yaw/pitch approximation for later joints, while the URDF has explicit joint axes including x-axis wrist rotations.

Therefore Stage 2.5 should end with:

- PyBullet closest-point collision fidelity implemented;
- geometry diagnostics available;
- calibration report explaining residual mismatch;
- recommendation to use backend-specific expectations or treat mock as a deterministic baseline rather than a PyBullet truth target.

## Verification

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage2_urdf_calibration.py -q --basetemp .pytest_tmp/current
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp/current
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.calibrate_urdf_geometry --task bench\sim_robot_arm\mid_trajectory_collision_001 --output-json output_reports\mid_trajectory_urdf_calibration.json
```
