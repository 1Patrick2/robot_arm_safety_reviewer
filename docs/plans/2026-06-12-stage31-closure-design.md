# Stage 3.1 Closure Design

## Goal

Close the application foundation work before adding PolicyAction, dataset adapters, visual sandboxing, metrics storage, or diagnostic agents.

## Scope

Stage 3.1 closure is limited to four outcomes:

1. Move duplicated CLI result formatting into `cli/output.py`.
2. Preserve existing legacy and unified CLI output contracts.
3. Document application boundary rules and agent adoption research.
4. Update the current project status so Stage 3.1 has a clear exit point.

## Architecture

CLI modules remain thin adapters. They parse arguments, build application request objects, call application services, and delegate all result printing to `cli.output`.

The `application` package stays as the reusable orchestration boundary. Lower-level packages such as `robot_runtime`, `robot_safety`, `sim`, and `gateway` must not import `application`, `agent`, or future `robot_tools`.

Research docs are pattern-first, not star-first. They record which external projects are useful for architecture ideas without making them runtime dependencies.

## Testing

Add focused tests for `cli.output` so JSON and text output remain compatible with the current CLI behavior. Existing CLI subprocess tests continue to protect the end-to-end command surface.
