# Agent Rules For This Repository

## Current Refactor Stage

The project is in Stage R1: architecture refactor.

R1-A defines the target layout and migration rules.
R1-B migrates robot-domain code in small, testable steps.

## Target Layout

- `robot/`: robot domain core. Contains robot models, kinematics, safety rules, runtime execution abstractions, backend adapters, and low-level safety evaluation logic.
- `perception/`: perception input and perception-to-safety observation layer. Contains perception result schema, loaders, fake/real adapters, and fusion rules.
- `diagnostics/`: diagnostic evidence and reporting layer. Contains context builders, evidence manifests, reports, diagnostic analysis, and regression contracts.
- `application/`: thin use-case orchestration layer. Calls robot, perception, diagnostics, runtime DB, and report modules.
- `cli/`: command-line interface only. No business logic.
- `bench/`: versioned fixtures and scenarios. No production code.
- `common/`: shared helpers only. No domain logic.

## Migration Rules

- Do not add new stage-named production directories.
- Put new robot safety code under `robot/`, not under legacy `robot_safety/`.
- Keep legacy import shims while migration is in progress.
- Move one domain slice at a time and run focused tests after each slice.
- Do not mix deterministic safety decisions with diagnostic or presentation logic.
- `robot/` must not depend on `diagnostics/`, `application/`, or `cli/`.
- `diagnostics/` may read robot and perception outputs, but must not control robot actions.
- `application/` may orchestrate lower layers but should stay thin.

## Current Compatibility State

- `robot/safety/` is the new home for the former `robot_safety` implementation.
- `robot_safety/` remains as a compatibility package and should only contain import shims.
- Existing callers may continue using `robot_safety.*` until their imports are migrated in later R1 steps.
