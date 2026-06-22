# Robot Action Safety Sandbox Main Prompt

Use this file as the project handoff prompt for new sessions.

## Project Identity

Project name: Robot Action Safety Sandbox.

Current positioning: robot action safety evaluation + diagnostic evidence framework.

This is not a generic Agent project. Optional LLM diagnostic analysis is an evidence explanation layer only.

Safety decisions are made by deterministic runtime logic, not by an LLM or agent.

## Current Stage

Completed through Stage 4.4-B.

Current architecture work: Stage R1 Project Architecture Refactor.

Stage 5.1 Perception Result Schema + Fake Perception Adapter is deferred until the R1 architecture rules and first robot-domain migration are stable.

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

- `robot/safety/` is the new home for the former `robot_safety` implementation.
- `robot_safety/` is now a compatibility shim package.
- New robot safety code should use `robot.safety.*`.
- Do not remove legacy shims until all imports are migrated and focused tests pass.

## Deferred Stage 5.1 Plan

Stage 5.1: Perception Result Schema + Fake Perception Adapter.

- Define `perception_result.json`.
- Validate detections.
- Convert person/object/zone/distance into structured safety observations.
- No ONNX/RKNN/camera yet.

## Operating Rules

- Keep deterministic safety decisions inside `SafetyRuntime` and existing safety evaluation layers.
- Keep diagnostic analysis read-only and evidence-based.
- Prefer small changes inside existing responsibility boundaries.
- Do not add real perception, edge inference, camera, ONNX, RKNN, or real LLM integration during Stage R1.
- For Stage 5.1, start with schema, fake adapter, and focused validation before any real model integration.
