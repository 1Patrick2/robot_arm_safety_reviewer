# Stage 2 URDF Asset Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a simplified mock RealMan-style 6-DOF URDF asset that can later be loaded by the PyBullet backend.

**Architecture:** Keep Stage 2.2 asset-only: no evaluator, backend factory, or gateway behavior changes. The URDF should mirror Stage 1 defaults closely enough for future PyBullet replay: six revolute joints, six moving links, simple collision geometry, default joint limits, and approximate link lengths.

**Tech Stack:** URDF XML, Python XML parsing tests, optional PyBullet smoke test using `pytest.importorskip("pybullet")`.

---

### Task 1: URDF Asset Tests

**Files:**
- Test: `tests/test_stage2_urdf.py`

**Step 1: Write failing tests**

Check that `assets/robots/mock_realman_6dof/robot.urdf` and README exist, parse as XML, define six revolute joints, expose expected joint limits, and include collision geometry.

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_stage2_urdf.py -q`

Expected: fail because the URDF asset does not exist.

### Task 2: URDF Asset

**Files:**
- Create: `assets/robots/mock_realman_6dof/robot.urdf`
- Create: `assets/robots/mock_realman_6dof/README.md`
- Create: `requirements-sim.txt`

**Step 1: Implement minimal asset**

Create a simple serial chain with six revolute joints, link names `base_link` and `link_1` through `link_6`, collision geometry, and joint limits matching Stage 1 defaults.

**Step 2: Run targeted tests**

Run: `python -m pytest tests/test_stage2_urdf.py -q`

Expected: pass, with PyBullet-specific test skipped when PyBullet is not installed.

**Step 3: Run regression**

Run:
- `python -m pytest -q`
- `python -m cli.run_benchmark --backend mock --bench bench\sim_robot_arm --log-dir logs\benchmark --output-json output_reports\stage1_benchmark_summary.json --output-md output_reports\stage1_benchmark_summary.md`

Expected: Stage 1.5 and Stage 2.1 behavior remains unchanged.
