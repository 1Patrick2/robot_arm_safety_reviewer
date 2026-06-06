# Project Current Status

## Current Progress

RobotArmSafetyReviewer is complete through Stage 2.5.

Completed:

- Stage 1: deterministic robot-arm safety gate
- Stage 1.5: benchmark, scorer, replay, and report loop
- Stage 2.1: backend abstraction
- Stage 2.2: mock RealMan-style URDF asset
- Stage 2.3: minimal PyBullet backend
- Stage 2.4: mock-vs-PyBullet backend comparison
- Stage 2.5A: PyBullet closest-point collision geometry
- Stage 2.5B: PyBullet geometry diagnostics
- Stage 2.5C: URDF-vs-mock calibration reporting

## Core Modules

- `robot_safety/models.py`: scene, command, violation, and safety result data models
- `robot_safety/evaluator.py`: safety review orchestration
- `robot_safety/safety_rules.py`: rule-based decision and risk logic
- `robot_safety/collision.py`: mock segment-sphere clearance checks
- `robot_safety/kinematics.py`: deterministic mock 6-DOF FK
- `sim/base.py`: simulation backend interface and result contract
- `sim/mock_backend.py`: deterministic mock geometry backend
- `sim/pybullet_backend.py`: PyBullet URDF replay and closest-point geometry backend
- `sim/pybullet_diagnostics.py`: per-step PyBullet geometry diagnostics
- `sim/urdf_calibration.py`: URDF-vs-mock calibration report
- `gateway/safety_gate.py`: review and execute-if-safe boundary
- `gateway/replay.py`: replayable log verification
- `reports/backend_comparison.py`: backend comparison summary
- `reports/report_writer.py`: Markdown report generation
- `cli/`: command-line entry points

## Current Verification

Latest verified commands:

```text
pytest -q
89 passed

python -m cli.run_benchmark --backend mock --bench bench/sim_robot_arm
8 passed, 0 failed

python -m cli.run_benchmark --backend pybullet --mode smoke --bench bench/sim_robot_arm
8 completed, 0 runtime errors

python -m cli.compare_backends --bench bench/sim_robot_arm --backends mock pybullet
decision_matches=8, risk_matches=8, strict_matches=6, backend_errors=0
```

## Known Technical Debt

- `last_review_metadata` is a pragmatic bridge from backend diagnostics into gateway logs. A future cleanup could replace it with a richer review outcome object.
- Mock FK is intentionally simplified and does not match the URDF kinematic model exactly.
- Benchmark expectations are currently mock-oriented; PyBullet results should eventually get backend-specific expectations.
- PyBullet backend currently supports sphere obstacles only.
- No self-collision, workspace boundary, speed/acceleration safety, GUI replay, RealMan SDK, ROS2, MoveIt, Agent, or LeRobot integration yet.

## Next Stage

Recommended next stage:

```text
Stage 2.6: backend-specific benchmark expectations
```

Goal:

- keep mock as deterministic regression baseline;
- add explicit PyBullet expectations where geometry differs;
- avoid forcing PyBullet to match the simplified mock FK model;
- prepare for later visual replay or Agent tooling with cleaner evaluation semantics.

## Suggested Code Reading Order

1. `README.md` and `docs/stage2_backend_diagnostics.md`
2. `robot_safety/models.py`, `robot_safety/evaluator.py`, `robot_safety/safety_rules.py`
3. `robot_safety/collision.py`, `robot_safety/kinematics.py`
4. `sim/base.py`, `sim/mock_backend.py`, `sim/pybullet_backend.py`
5. `gateway/safety_gate.py`, `gateway/execution_logger.py`, `gateway/replay.py`
6. `robot_safety/benchmark.py`, `robot_safety/scorer.py`, `reports/backend_comparison.py`
7. `sim/pybullet_diagnostics.py`, `sim/urdf_calibration.py`
