# Agent Project Radar

This radar tracks projects by architectural pattern, not popularity. The goal is to learn useful boundaries for diagnostics, traces, tools, and dataset-backed runtime evaluation without turning RobotArmSafetyReviewer into a general agent framework or robot learning stack.

| Project | Category | Pattern to learn | Fit for this project | Decision | Reason |
|---|---|---|---|---|---|
| OpenAI Agents SDK | Agent framework | Tool contracts, handoffs, tracing, structured outputs | Medium | Watch | Useful for future diagnostic tooling, but the current project should stay deterministic until metrics and failure traces are stable. |
| LangGraph / LangSmith | Agent workflow and observability | Graph state, durable traces, evaluation dashboards | Medium | Watch | Good reference for trace and run-state design; dependency and scope are too large for Stage 3.1-3.6. |
| smolagents | Lightweight agent tools | Minimal tool invocation and simple agent loop | Medium | Watch | Good low-complexity reference for a future single diagnostic agent. |
| OpenHands | Coding agent | Workspace actions, tool traces, task isolation | Low | Reject for runtime | Useful as a context-management reference only; this project must not become a coding agent. |
| AutoGen / AutoGen Studio | Multi-agent orchestration | Role separation and conversation traces | Low | Reject for near term | Multi-agent orchestration is unnecessary before deterministic metrics and tool APIs exist. |
| browser-use | Browser automation agent | External tool boundary and replayable actions | Low | Watch | Useful as a tool-boundary example, not as a runtime dependency. |
| OpenManus / Manus-like projects | General autonomous agents | Task decomposition and tool routing | Low | Reject for near term | Too broad; the project needs constrained diagnostics, not autonomous execution. |
| LeRobot | Robot learning dataset/runtime | Dataset episode conventions and action/state schema | High | Adopt patterns | Strong reference for local dataset sample layout and action-sequence conversion. |
| RoboMimic | Robot imitation dataset | HDF5 episode structure and action/state arrays | Medium | Watch | Good future adapter target after `PolicyActionSequence` is stable. |
| DROID | Robot demonstration dataset | Real-world episode metadata and language instructions | Medium | Watch | Useful for dataset-backed evaluation concepts, not needed for MVP. |
| BridgeData | Robot dataset | Task/language/action dataset structure | Medium | Watch | Useful for adapter design once local samples work. |
| Open X-Embodiment | Multi-robot dataset collection | Cross-dataset action/state normalization | Medium | Watch | Important long-term reference, but too broad for initial adapter work. |

## Screening Rules

- Prefer pattern-first evaluation over star count.
- Track runtime object models, tool interfaces, traces, guardrails, CLI/API reuse, tests, and dependency cost.
- Adopt ideas incrementally only when they support deterministic safety review, runtime metrics, or diagnostic explanation.
