# Robot Action Safety Sandbox Main Prompt

Use this file as the project handoff prompt for new sessions.

## Project Identity

Project name: Robot Action Safety Sandbox.

Current positioning: robot action safety evaluation + diagnostic evidence framework.

This is not a generic Agent project. Optional LLM diagnostic analysis is an evidence explanation layer only.

Safety decisions are made by deterministic runtime logic, not by an LLM or agent.

## Current Stage

Completed through Stage 5.3-A.

Current architecture work: Stage R1 Project Architecture Refactor completed.

Completed R1 robot-domain migration:

- R1-B1: `robot_safety` implementation moved to `robot/safety`.
- R1-B2: `robot_runtime` implementation moved to `robot/runtime`.
- R1-B3: `sim` backend core moved to `robot/backends`.
- R1-B4: `robots` implementation moved to `robot/adapters`.
- R1-B5: internal imports migrated to `robot.*`.
- R1-B6: legacy robot packages (`robot_safety/`, `robot_runtime/`, `robots/`) removed.
- `sim/` backend core shims (`base.py`, `backend_factory.py`, `mock_backend.py`, `pybullet_backend.py`) removed.
- `sim/` backend core shims and diagnostic geometry modules are now compatibility shims (moved to `diagnostics/geometry/`).
- `diagnostics/` is now the canonical diagnostics package, containing context, tools, report, evidence/manifest, runtime, agent, guardrails, analysis, contracts, and geometry sub-packages.
- `reports/evidence_manifest.py` is compatibility-only (implementation at `diagnostics/evidence/manifest.py`).

Current recommended task:

- R1-C validation and polish: stabilize the diagnostics migration, update documentation.

Paused feature work:

- Stage 5.3-B Perception-Aware Regression Summary Integration is paused until R1-C validation passes.
- Model adapter / ONNX / RKNN work is out of scope until R1-C is stable.

## Completed Capabilities

- SafetyRuntime.
- PolicyActionSequence.
- mock / PyBullet backend.
- runtime metrics DB.
- diagnostic context.
- deterministic report.
- evidence_manifest.
- evidence_groups.
- expected_contract.
- diagnostic regression.
- Level-2 safety scenarios.
- fake diagnostic analyst.
- diagnostic analysis service.
- diagnostic analyze CLI.
- perception_result.v1 schema and loader.
- fake perception adapter.
- perception safety fusion rules.
- perception-aware regression fixtures.

## Hard Boundaries

- LLM must not approve/reject.
- LLM must not modify actions.
- LLM must not execute robot actions.
- LLM must not replace SafetyRuntime.
- The project is not a motion planner.
- The project is not a generic Agent framework.
- The project is not an edge deployment project yet.

## Current Strategic Shift

Do not continue expanding generic Agent features.

Stop deepening multi-agent / real LLM provider work for now.

Near-term direction is architecture cleanup before more perception-aware safety fusion features.

Perception can start from structured JSON / fake adapter; no edge deployment required initially.

## Architecture Refactor Rules

Target top-level domains:

- `robot/`: robot models, kinematics, safety rules, runtime abstractions, backends, and adapters.
- `perception/`: perception result schema, loaders, fake/real adapters, and fusion rules.
- `diagnostics/`: diagnostic context, evidence manifests, reports, analysis, and regression contracts.
- `application/`: thin orchestration services.
- `cli/`: command-line interface only.
- `bench/`: fixtures and scenarios only.
- `common/`: shared helpers only.

Current R1 migration state:

- R1-B6 completed.
- `robot/` is the only canonical robot-domain package.
- Legacy packages `robot_safety/`, `robot_runtime/`, `robots/` have been removed.
- `sim/` backend core shims have been removed.
- `sim/` temporarily retains only diagnostic geometry utilities pending R1-C.
- All internal imports now use `robot.*` paths.

## Completed Stage 5 Perception Work

- Stage 5.1: perception_result.v1 schema, loader, fake adapter.
- Stage 5.1-polish: unknown safe zone and distance threshold cleanup.
- Stage 5.2: perception safety fusion.
- Stage 5.2-polish: fusion edge-case coverage.
- Stage 5.3-A: perception-aware scenario fixtures and focused tests.

## Operating Rules

- Keep deterministic safety decisions inside `SafetyRuntime` and existing safety evaluation layers.
- Keep diagnostic analysis read-only and evidence-based.
- Prefer small changes inside existing responsibility boundaries.
- Do not add real perception, edge inference, camera, ONNX, RKNN, or real LLM integration during Stage R1.
- For Stage 5.1, start with schema, fake adapter, and focused validation before any real model integration.
