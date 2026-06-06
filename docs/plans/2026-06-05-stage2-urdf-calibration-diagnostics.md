# Stage 2.5B URDF Calibration Diagnostics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add structured PyBullet geometry diagnostics so remaining mock-vs-PyBullet differences can be explained through link poses, closest-point pairs, and URDF collision geometry attribution.

**Architecture:** Keep the safety review path unchanged. Add a diagnostics module that loads the same task inputs, replays the trajectory in PyBullet DIRECT mode, records per-step link poses, records closest-point observations against sphere obstacles, and summarizes the worst geometry pair. Add a small CLI wrapper that prints JSON or writes it to disk.

**Tech Stack:** Python dataclasses/dicts, PyBullet DIRECT mode, existing `Scene`/`JointCommand` models, existing trajectory interpolation, pytest.

---

### Task 1: Add Diagnostics Tests

**Files:**
- Create: `tests/test_stage2_pybullet_diagnostics.py`
- Read: `bench/sim_robot_arm/mid_trajectory_collision_001/scene.json`
- Read: `bench/sim_robot_arm/mid_trajectory_collision_001/command.json`

**Step 1: Write failing tests**

Test behaviors:

- `diagnose_task_geometry(task_dir)` returns a JSON-serializable dict;
- output includes `task_id`, `backend`, `collision_method`, `checked_links`, `steps`, and `worst_pair`;
- each step has `step`, `joints`, `link_poses`, and `closest_points`;
- `mid_trajectory_collision_001` has a meaningful `worst_pair`;
- CLI can write a JSON file.

**Step 2: Run tests to verify failure**

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage2_pybullet_diagnostics.py -q --basetemp .pytest_tmp/current
```

Expected: import failure for missing `sim.pybullet_diagnostics`.

### Task 2: Implement Diagnostics Module

**Files:**
- Create: `sim/pybullet_diagnostics.py`
- Read/reuse: `sim/pybullet_backend.py`

**Implementation requirements:**

- function:

```python
def diagnose_task_geometry(task_dir: str | Path, *, backend: PyBulletBackend | None = None) -> dict[str, Any]:
```

- load `Scene` and `JointCommand`;
- build trajectory with existing interpolation;
- run PyBullet in DIRECT;
- load the configured URDF;
- create sphere obstacle bodies;
- build link map using the same backend setting;
- for each trajectory step:
  - reset revolute joint states;
  - call `performCollisionDetection`;
  - record link world poses;
  - record closest-point observations returned by `getClosestPoints`;
- return only JSON-serializable primitives;
- summarize `worst_pair` from the minimum contact distance.

### Task 3: Implement CLI

**Files:**
- Create: `cli/diagnose_backend_geometry.py`

**CLI behavior:**

```powershell
python -m cli.diagnose_backend_geometry --task bench\sim_robot_arm\mid_trajectory_collision_001
```

Options:

- `--task`: required task directory;
- `--output-json`: optional output file;
- `--include-base-collision`: optional flag;
- `--search-distance`: optional float defaulting to backend default;
- `--indent`: optional JSON indent, default `2`.

Print a concise summary to stdout:

```text
Geometry Diagnostics
Task: mid_trajectory_collision_001
Backend: pybullet
Collision Method: pybullet_closest_points_sphere_collision
Worst Pair: step=5 link=link_3 obstacle=sphere_mid clearance=0.045865
```

When `--output-json` is provided, write the full structured diagnostic JSON.

### Task 4: Update Documentation

**Files:**
- Modify: `docs/stage2_backend_diagnostics.md`

Add Stage 2.5B section:

- command used to generate diagnostics;
- worst pair for `mid_trajectory_collision_001`;
- checked links;
- interpretation: remaining mismatch is geometry calibration, not backend runtime failure.

### Task 5: Verification

Run focused tests:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage2_pybullet_diagnostics.py -q --basetemp .pytest_tmp/current
```

Run full tests:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp/current
```

Run benchmark checks:

```powershell
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.run_benchmark --backend pybullet --mode smoke
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.run_benchmark --backend mock
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.compare_backends --bench bench\sim_robot_arm --backends mock pybullet --output-json output_reports\backend_comparison.json --output-md output_reports\backend_comparison.md
```

Run diagnostics CLI:

```powershell
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.diagnose_backend_geometry --task bench\sim_robot_arm\mid_trajectory_collision_001 --output-json output_reports\mid_trajectory_geometry_diagnostics.json
```

Expected:

- diagnostics test passes;
- full pytest passes;
- PyBullet smoke completes 8/8;
- mock scored benchmark passes 8/8;
- backend comparison has 0 backend errors;
- diagnostics JSON records `worst_pair` with a non-null link, obstacle, step, and clearance.
