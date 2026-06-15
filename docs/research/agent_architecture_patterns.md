# Agent Architecture Patterns

This project should borrow agent architecture patterns only where they improve diagnostic evidence handling. Agents must not own safety decisions or robot execution.

## Patterns To Adopt

## Tool Boundary

Future agents call project tools. Project tools call application services. Agents do not call `RobotDeviceAdapter.send_action()`.

```text
Diagnostic Agent
  -> robot_tools
    -> application services
      -> deterministic safety/runtime code
```

## Structured Evidence Package

Future diagnostic prompts should receive a compact evidence package:

- run id;
- question;
- relevant metrics;
- failed step summary;
- artifact paths;
- project safety rules;
- allowed tools.

This avoids passing full logs or long conversation history directly to the model.

## Trace Every Tool Call

Each future agent tool call should record:

- tool name;
- structured input;
- structured output;
- elapsed time;
- success or error.

The trace is evidence for debugging and interview explanation. It is not part of the safety decision.

## Compact Summaries

Long diagnostic sessions should summarize prior context into a compact file. The model should read the summary and selected artifacts, not the full raw conversation.

## Patterns To Avoid

- Autonomous robot control.
- LLM approve/reject decisions.
- Multi-agent orchestration before deterministic metrics exist.
- Direct model access to robot execution adapters.
- Unbounded recursive subtasks.
