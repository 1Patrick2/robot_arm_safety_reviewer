# Stage 3.2 PolicyAction Interface Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the first policy action sequence model and conversion layer.

**Architecture:** `robot_runtime.policy_action` owns the action dataclass and conversion to `RobotAction`. `robot_runtime.action_sequence` owns sequence serialization and JSON file loading. Samples live under `samples/policy_sequences`.

**Tech Stack:** Python dataclasses, pathlib/json from the standard library, pytest.

---

### Task 1: PolicyAction Tests

**Files:**
- Create: `tests/test_stage32_policy_action.py`

**Steps:**
1. Write tests for JSON loading, `to_dict`, `joint_target` conversion, `delta_joint` conversion, invalid action type, and dimension mismatch.
2. Run: `python -m pytest tests/test_stage32_policy_action.py -q --basetemp D:\tmp\pytest-stage32-red`
3. Expected: FAIL because modules do not exist.

### Task 2: PolicyAction Implementation

**Files:**
- Create: `robot_runtime/policy_action.py`
- Create: `robot_runtime/action_sequence.py`
- Modify: `robot_runtime/__init__.py`

**Steps:**
1. Implement immutable dataclasses and validation.
2. Implement JSON loading and dict serialization.
3. Implement `policy_action_to_robot_action`.
4. Run focused tests until green.

### Task 3: Samples and Documentation

**Files:**
- Create: `samples/policy_sequences/simple_safe_sequence.json`
- Create: `samples/policy_sequences/near_miss_sequence.json`
- Create: `samples/policy_sequences/collision_sequence.json`
- Modify: `docs/core_function_map.md`
- Modify: `docs/project_current_status.md`

**Steps:**
1. Add minimal local sequence fixtures.
2. Document new modules and Stage 3.2 status.
3. Run focused and full tests.
