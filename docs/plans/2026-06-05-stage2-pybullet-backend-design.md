# Stage 2.3 PyBullet Backend Design

## Goal

Build a minimal PyBullet simulation backend that can run through the existing `SimulationBackend` interface and validate joint-space safety review against the project URDF asset.

## Recommended Approach

Use a narrow PyBullet backend that loads `assets/robots/mock_realman_6dof/robot.urdf`, replays interpolated joint trajectories with `resetJointState`, samples link world positions, and computes clearance against the existing sphere obstacle format. This keeps the backend deterministic, testable, and comparable with the current mock backend.

Alternative approaches were considered:

- Full PyBullet collision queries: more realistic, but requires careful obstacle body creation, collision filtering, and interpretation of contact distances.
- GUI replay first: useful for demos, but it adds non-essential runtime and display assumptions.
- RealMan-like calibration: not appropriate yet because the current URDF is a simplified mock asset.

The recommended approach is the smallest step that proves the backend abstraction is useful while keeping Stage 1.5 behavior intact.

## Scope

Included:

- `create_backend("pybullet")`
- `sim/pybullet_backend.py`
- URDF loading in DIRECT mode
- Joint-state trajectory replay
- Sphere obstacle clearance using PyBullet link positions
- CLI support for `--backend pybullet`
- Tests that skip cleanly when PyBullet is unavailable

Not included:

- PyBullet GUI replay
- dynamic simulation, gravity, motors, velocity, or acceleration checks
- exact mesh collision
- self-collision
- RealMan hardware or SDK integration
- ROS2 / MoveIt planning-scene integration

## Data Flow

```text
scene.json + command.json
  -> robot_safety.evaluate_joint_command(..., backend=PyBulletBackend)
  -> trajectory interpolation
  -> PyBulletBackend.replay_joint_trajectory(...)
  -> BackendReviewResult
  -> safety_rules.decide_safety(...)
  -> SafetyResult
  -> gateway log / benchmark / report
```

The backend must return the same `BackendReviewResult` fields as `MockGeometryBackend`:

- `backend_name`
- `collision_free`
- `min_clearance`
- `closest_robot_link`
- `closest_obstacle`
- `worst_step`
- `violations`
- `metadata`

The initial PyBullet backend uses link-frame position sampling for sphere clearance. It does not yet use full PyBullet contact or closest-point queries over collision geometry. This is a backend validation method for URDF loading and trajectory replay, not exact mesh collision checking.

Every execution log generated with a backend should keep reproducibility metadata. PyBullet logs should include backend name, DIRECT mode, URDF path, and the clearance method. Mock logs should keep the existing mock model version and segment-sphere clearance method.

All Stage 2 tests should use the existing `Scene` and `JointCommand` schema. Prefer loading benchmark fixtures with `Scene.from_json(...)` and `JointCommand.from_json(...)` instead of introducing a separate test-only scene schema.

## Error Handling

If PyBullet is not installed, importing or creating the backend should fail with a clear message that tells the user to install the simulation dependencies. Tests that require PyBullet should use `pytest.importorskip("pybullet")`.

If the URDF file is missing or cannot be loaded, the backend should raise a descriptive runtime error. This is a project configuration error, not a safety-review decision.

## Testing Strategy

Use TDD around the backend boundary:

- factory returns `PyBulletBackend` for `pybullet`
- backend exposes `name == "pybullet"`
- backend can load the mock RealMan URDF
- backend returns a valid `BackendReviewResult` for a simple benchmark trajectory
- CLI accepts `--backend pybullet`
- full tests still pass for the mock backend

The first PyBullet benchmark result does not need to numerically match the mock backend. The important requirement is that the pipeline runs end to end and returns structured safety-review output.
