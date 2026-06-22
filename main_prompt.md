# Robot Action Safety Sandbox Main Prompt

Use this file as the project handoff prompt for new sessions.

## Project Identity

Project name: Robot Action Safety Sandbox.

Current positioning: robot action safety evaluation + diagnostic evidence framework.

This is not a generic Agent project. Optional LLM diagnostic analysis is an evidence explanation layer only.

Safety decisions are made by deterministic runtime logic, not by an LLM or agent.

## Current Stage

Completed through Stage 4.4-B.

Current documentation sync: Stage 4.4-D.

Next major stage: Stage 5.1 Perception Result Schema + Fake Perception Adapter.

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

Next direction is perception-aware safety fusion.

Perception can start from structured JSON / fake adapter; no edge deployment required initially.

## Next Stage Plan

Stage 5.1: Perception Result Schema + Fake Perception Adapter.

- Define `perception_result.json`.
- Validate detections.
- Convert person/object/zone/distance into structured safety observations.
- No ONNX/RKNN/camera yet.

## Operating Rules

- Keep deterministic safety decisions inside `SafetyRuntime` and existing safety evaluation layers.
- Keep diagnostic analysis read-only and evidence-based.
- Prefer small changes inside existing responsibility boundaries.
- Do not add real perception, edge inference, camera, ONNX, RKNN, or real LLM integration during Stage 4.4-D.
- For Stage 5.1, start with schema, fake adapter, and focused validation before any real model integration.
