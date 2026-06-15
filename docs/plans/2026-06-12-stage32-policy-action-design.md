# Stage 3.2 PolicyAction Interface Design

## Goal

Introduce a stable action-sequence input contract so future dataset adapters, policy rollouts, and sequence runtimes do not depend on benchmark `command.json` files.

## Scope

Stage 3.2 adds:

1. `PolicyAction` for one policy-proposed action.
2. `PolicyActionSequence` for a small ordered rollout.
3. JSON load/save helpers for local fixtures.
4. Conversion from `PolicyAction` to runtime `RobotAction`.
5. Three sample policy sequences.

The first supported action types are `joint_target` and `delta_joint`.

## Non-Goals

Stage 3.2 does not add sequence execution, dataset adapters, PyBullet robot-device control, metrics storage, or agent diagnostics.

It also does not support `ee_pose`, `gripper`, `mobile_base`, force control, or vision-conditioned actions.

## Conversion Rules

- `joint_target`: `values` become `RobotAction.target_joints`.
- `delta_joint`: `values` are added to `RobotObservation.joint_positions`.
- Both require exactly six numeric values.
- Unsupported action types fail before creating a `RobotAction`.
