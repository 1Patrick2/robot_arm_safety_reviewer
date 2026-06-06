# Stage 2 Backend Abstraction Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a backend abstraction so the existing safety evaluator can run through a mock geometry backend now and a PyBullet backend later.

**Architecture:** Keep the current Stage 1.5 safety behavior unchanged by wrapping the existing FK/collision pipeline in `MockGeometryBackend`. The evaluator will still own command validation, joint interpolation, joint limit checks, risk classification, and `SafetyResult` construction, but it will obtain collision and clearance evidence through a `SimulationBackend`.

**Tech Stack:** Python dataclasses, typing `Protocol`, pytest, existing CLI modules.

---

### Task 1: Backend Model And Factory

**Files:**
- Create: `sim/__init__.py`
- Create: `sim/base.py`
- Create: `sim/mock_backend.py`
- Create: `sim/backend_factory.py`
- Test: `tests/test_stage2_backend_factory.py`

**Step 1: Write failing tests**

Test that `create_backend("mock")` returns a backend named `mock`, and that an unsupported backend raises `ValueError`.

**Step 2: Run targeted test**

Run: `python -m pytest tests/test_stage2_backend_factory.py -q`

Expected: fail because `sim.backend_factory` does not exist.

**Step 3: Implement minimal backend**

Define `BackendReviewResult`, `SimulationBackend`, `MockGeometryBackend`, and `create_backend`.

**Step 4: Run targeted test**

Run: `python -m pytest tests/test_stage2_backend_factory.py -q`

Expected: pass.

### Task 2: Evaluator Backend Injection

**Files:**
- Modify: `robot_safety/evaluator.py`
- Test: `tests/test_stage2_mock_backend.py`

**Step 1: Write failing tests**

Test that `evaluate_joint_command(scene, command, backend=create_backend("mock"))` matches the existing default evaluator result for a benchmark task.

**Step 2: Run targeted test**

Run: `python -m pytest tests/test_stage2_mock_backend.py -q`

Expected: fail because `evaluate_joint_command` does not accept `backend`.

**Step 3: Wire evaluator to backend**

Use `backend or MockGeometryBackend()` and replace direct trajectory collision calls with `backend.replay_joint_trajectory(scene=scene, trajectory=trajectory)`.

**Step 4: Run targeted test**

Run: `python -m pytest tests/test_stage2_mock_backend.py -q`

Expected: pass.

### Task 3: Gateway And CLI Backend Option

**Files:**
- Modify: `gateway/safety_gate.py`
- Modify: `gateway/execution_logger.py`
- Modify: `robot_safety/benchmark.py`
- Modify: `cli/review_command.py`
- Modify: `cli/execute_if_safe.py`
- Modify: `cli/run_benchmark.py`
- Test: `tests/test_stage2_backend_cli.py`

**Step 1: Write failing tests**

Test that `review_only(..., backend_name="mock")` records `review_backend.name == "mock"` in the execution log. Test that the CLI accepts `--backend mock`.

**Step 2: Run targeted test**

Run: `python -m pytest tests/test_stage2_backend_cli.py -q`

Expected: fail because backend arguments and log metadata do not exist.

**Step 3: Implement CLI and log wiring**

Pass `backend_name` through the gateway and benchmark runner, create the backend through the factory, and add `review_backend` metadata to logs.

**Step 4: Run targeted and full verification**

Run:
- `python -m pytest tests/test_stage2_backend_cli.py -q`
- `python -m pytest -q`
- `python -m cli.run_benchmark --backend mock --bench bench\sim_robot_arm --log-dir logs\benchmark --output-json output_reports\stage1_benchmark_summary.json --output-md output_reports\stage1_benchmark_summary.md`

Expected: all existing Stage 1.5 behavior remains unchanged under the mock backend.
