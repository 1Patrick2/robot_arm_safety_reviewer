# Agent Rules For This Repository

## Current Refactor Stage

The project is in Stage R1: architecture refactor.

R1-A defines the target layout and migration rules.
R1-B migrates robot-domain code in small, testable steps.

## Target Layout

- `robot/`: robot domain core. Contains robot models, kinematics, safety rules, runtime execution abstractions, backend adapters, and low-level safety evaluation logic. This is the only canonical robot-domain package.
- `perception/`: perception input and perception-to-safety observation layer. Contains perception result schema, loaders, fake/real adapters, and fusion rules.
- `diagnostics/`: diagnostic evidence and reporting layer. Contains context builders, evidence manifests, reports, diagnostic analysis, and regression contracts.
- `application/`: thin use-case orchestration layer. Calls robot, perception, diagnostics, runtime DB, and report modules.
- `cli/`: command-line interface only. No business logic.
- `bench/`: versioned fixtures and scenarios. No production code.
- `common/`: shared helpers only. No domain logic.

## Migration Rules

- Do not add new stage-named production directories.
- Put new robot safety code under `robot/`.
- Move one domain slice at a time and run focused tests after each slice.
- Do not mix deterministic safety decisions with diagnostic or presentation logic.
- `robot/` must not depend on `diagnostics/`, `application/`, or `cli/`.
- `diagnostics/` may read robot and perception outputs, but must not control robot actions.
- `application/` may orchestrate lower layers but should stay thin.

## Refactor Commit Rules

- Do not combine architecture-rule changes and code migration in the same commit.
- Do not move more than one domain slice per commit.
- Legacy robot packages (`robot_safety/`, `robot_runtime/`, `robots/`) have been removed after R1-B6. All code must use `robot.*` imports.
- Production code must not be placed in stage-numbered directories.
- New production directories must fit the target layout in this file.
- If a file does not clearly belong to a target layer, stop and document the intended ownership before moving it.

## Current Robot Domain State

- `robot/safety/` is the new home for the former `robot_safety` implementation. The legacy `robot_safety/` package has been removed after R1-B6.
- `robot/runtime/` is the canonical runtime package. Legacy `robot_runtime/` has been removed.
- `robot/backends/` is the canonical backend package. Legacy `sim/base.py`, `sim/backend_factory.py`, `sim/mock_backend.py`, `sim/pybullet_backend.py` shims have been removed.
- `robot/adapters/` is the canonical adapter package. Legacy `robots/` has been removed.
- `sim/` temporarily contains only diagnostic geometry utilities (`pybullet_diagnostics.py`, `urdf_calibration.py`) pending R1-C ownership decision.
- New implementation code must use `robot.*` imports.
