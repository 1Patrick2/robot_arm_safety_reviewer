# Adoption Decisions

This file records explicit choices so future work does not expand scope by accident.

## Adopt Now

### Application Service Boundary

All new CLI, batch, dataset, sandbox, database, and future agent surfaces should call application services instead of rebuilding runtime objects directly.

### Shared CLI Output

CLI commands should use `cli.output` for common JSON and text formatting. Command modules should only parse arguments, create requests, call services, and print results.

### Pattern-First Research

Research docs should compare architecture patterns, not chase popular repositories. Useful patterns include tool boundaries, trace logging, dataset episode schemas, and evaluation summaries.

## Watch

### LeRobot-Style Dataset Layouts

Useful for Stage 3.4 local sample adapters after Stage 3.2 introduces `PolicyActionSequence`.

### RoboMimic HDF5 Structure

Useful after JSON-based mini sequences are stable. HDF5 support should be optional and skipped in tests when `h5py` is unavailable.

### Agent Tool Frameworks

OpenAI Agents SDK, LangGraph, and smolagents are useful references for tool schemas and traces, but should not be dependencies before runtime metrics are queryable.

## Reject For Current Stage

### LLM Safety Decision Making

Safety decisions must stay deterministic. Future agents can explain decisions, not replace them.

### Direct RealMan Execution

Real hardware work must wait for dry-run and shadow-mode stages.

### General Autonomous Agent Scope

The project is a robot action safety sandbox and diagnostics system, not a general coding agent, browser agent, or multi-agent platform.
