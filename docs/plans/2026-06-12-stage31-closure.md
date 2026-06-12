# Stage 3.1 Closure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Close Stage 3.1 by centralizing CLI output, documenting boundaries, and adding agent research radar docs.

**Architecture:** CLI commands call application services and delegate formatting to `cli.output`. Documentation records package boundaries and future adoption decisions without adding new runtime dependencies.

**Tech Stack:** Python dataclasses, pytest, argparse CLIs, Markdown documentation.

---

### Task 1: CLI Output Tests

**Files:**
- Create: `tests/test_stage31_cli_output.py`

**Step 1: Write failing tests**

Test that runtime and review result text output keeps the existing field labels, and JSON output serializes `to_dict()` payloads.

**Step 2: Run focused tests**

Run: `python -m pytest tests/test_stage31_cli_output.py -q`

Expected: FAIL because `cli.output` does not exist.

### Task 2: CLI Output Module

**Files:**
- Create: `cli/output.py`
- Modify: `cli/commands/runtime.py`
- Modify: `cli/commands/review.py`
- Modify: `cli/run_runtime_demo.py`

**Step 1: Implement minimal output helpers**

Add `print_json`, `print_runtime_task_result`, and `print_review_command_result`.

**Step 2: Wire existing CLIs**

Replace duplicated JSON and text printing with calls to `cli.output`.

**Step 3: Run focused tests**

Run: `python -m pytest tests/test_stage31_cli_output.py tests/test_stage31_unified_cli.py tests/test_stage3_runtime_demo_cli.py -q`

Expected: PASS.

### Task 3: Boundary and Research Docs

**Files:**
- Modify: `docs/project_architecture.md`
- Modify: `docs/core_function_map.md`
- Modify: `docs/project_current_status.md`
- Create: `docs/research/agent_project_radar.md`
- Create: `docs/research/agent_architecture_patterns.md`
- Create: `docs/research/adoption_decisions.md`

**Step 1: Document boundaries**

Record allowed imports and the rule that agents may only diagnose through tool/application boundaries.

**Step 2: Add research radar docs**

Create concise pattern-first notes for agent frameworks and robot dataset projects.

### Task 4: Verification

**Files:**
- No new files.

**Step 1: Run focused Stage 3.1 tests**

Run: `python -m pytest tests/test_stage31_cli_output.py tests/test_stage31_application_core.py tests/test_stage31_runtime_service.py tests/test_stage31_unified_cli.py tests/test_stage3_runtime_demo_cli.py -q`

Expected: PASS.

**Step 2: Run full test suite**

Run: `python -m pytest -q`

Expected: PASS, except optional environment skips for unavailable PyBullet.
