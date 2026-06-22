# R1-C: Diagnostics Package Migration Plan

> **Status:** Planning document.  
> **Previous:** R1-B6 completed — robot domain is canonical under `robot/`.  
> **Next:** R1-C migrates diagnostics-related code into a unified `diagnostics/` package.

---

## 1. Motivation

After R1-B6, the robot domain is cleanly organized under `robot/`. However, diagnostics-related code remains scattered:

| Current Location | Role |
|---|---|
| `diagnostic_runtime/` | Context, tools, report, agent, guardrails, runtime orchestration |
| `reports/evidence_manifest.py` | Evidence manifest builder |
| `reports/runtime_episode_report.py` | Episode report (partially diagnostics) |
| `reports/runtime_visual_report.py` | Visual evidence (partially diagnostics) |
| `application/diagnostic_service.py` | Service orchestration for diagnostics |
| `application/diagnostic_analysis_service.py` | LLM diagnostic analysis service |
| `application/diagnostic_contracts.py` | Expected contract types and validation |
| `sim/pybullet_diagnostics.py` | Backend geometry diagnostics |
| `sim/urdf_calibration.py` | URDF calibration diagnostics |

This fragmentation makes it hard to enforce the rule that diagnostics must not control robot actions or affect safety decisions.

---

## 2. Target Layout

```
diagnostics/
  __init__.py
  context/
    models.py (from diagnostic_runtime/context/models.py)
    builder.py (from diagnostic_runtime/context/builder.py)
    render.py (from diagnostic_runtime/context/render.py)
  tools/
    context_tools.py (from diagnostic_runtime/tools/context_tools.py)
  report/
    deterministic.py (from diagnostic_runtime/report/deterministic.py)
  runtime/
    models.py (from diagnostic_runtime/runtime/models.py)
    runner.py (from diagnostic_runtime/runtime/runner.py)
    trace.py (from diagnostic_runtime/runtime/trace.py)
  evidence/
    manifest.py (from reports/evidence_manifest.py)
  agent/
    prompt.py (from diagnostic_runtime/agent/prompt.py)
    runner.py (from diagnostic_runtime/agent/runner.py)
    adapters/
      fake.py (from diagnostic_runtime/agent/adapters/fake.py)
      deepseek.py (from diagnostic_runtime/agent/adapters/deepseek.py)
  guardrails/
    safety_check.py (from diagnostic_runtime/guardrails/safety_check.py)
  analysis/
    models.py (from diagnostic_runtime/analysis/models.py)
    evidence_refs.py (from diagnostic_runtime/analysis/evidence_refs.py)
    fake_analyst.py (from diagnostic_runtime/analysis/fake_analyst.py)
  contracts/
    __init__.py (new)
    expected.py (from application/diagnostic_contracts.py)
  geometry/
    pybullet_diagnostics.py (from sim/pybullet_diagnostics.py)
    urdf_calibration.py (from sim/urdf_calibration.py)
```

### What stays outside

These files are **application orchestration**, not diagnostics domain logic:

| File | Reason |
|---|---|
| `application/diagnostic_service.py` | Orchestration layer, calls diagnostics modules |
| `application/diagnostic_analysis_service.py` | Orchestration layer, calls diagnostics analysis |
| `reports/runtime_episode_report.py` | Episode formatting, not diagnostic evidence |
| `reports/runtime_visual_report.py` | Visual artifact generation, not diagnostic evidence |
| `reports/backend_comparison.py` | Backend comparison, not diagnostic evidence |
| `reports/report_writer.py` | Legacy report format, pending deprecation |
| `reports/plot_3d.py` | Plotting utility, not diagnostic evidence |

---

## 3. Migration Order

### R1-C1: Scaffold + Compatibility Shim (this planning document)

- Create `diagnostics/` directory structure (empty `__init__.py` per sub-package).
- No code moved yet.
- **No tests change.**

### R1-C2: diagnostic_runtime/context -> diagnostics/context

**Move:**
- `diagnostic_runtime/context/models.py` → `diagnostics/context/models.py`
- `diagnostic_runtime/context/builder.py` → `diagnostics/context/builder.py`
- `diagnostic_runtime/context/render.py` → `diagnostics/context/render.py`

**Leave shim at:** `diagnostic_runtime/context/__init__.py` → `from diagnostics.context import *`
**Update imports in:** `application/agent_context_service.py`
**Test command:** `python -m pytest tests/test_stage37_agent_context_*.py -q`

### R1-C3: diagnostic_runtime/tools + report -> diagnostics/tools + report

**Move:**
- `diagnostic_runtime/tools/context_tools.py` → `diagnostics/tools/context_tools.py`
- `diagnostic_runtime/report/deterministic.py` → `diagnostics/report/deterministic.py`

**Test command:** `python -m pytest tests/test_diagnostics_tools.py tests/test_diagnostics_report.py -q`

### R1-C4: reports/evidence_manifest.py -> diagnostics/evidence/manifest.py

**Move:**
- `reports/evidence_manifest.py` → `diagnostics/evidence/manifest.py`

**Update imports in:** `application/diagnostic_service.py`
**The `reports/` package should keep a shim import.**
**Test command:** `python -m pytest tests/test_evidence_manifest.py -q`

### R1-C5: diagnostic_runtime/runtime -> diagnostics/runtime

**Move:**
- `diagnostic_runtime/runtime/models.py` → `diagnostics/runtime/models.py`
- `diagnostic_runtime/runtime/runner.py` → `diagnostics/runtime/runner.py`
- `diagnostic_runtime/runtime/trace.py` → `diagnostics/runtime/trace.py`

**Update imports in:** `application/diagnostic_service.py`
**Test command:** `python -m pytest tests/test_diagnostic_runtime_runner.py tests/test_diagnostic_runtime_integration.py -q`

### R1-C6: diagnostic_runtime/agent + guardrails -> diagnostics/agent + guardrails

**Move:**
- `diagnostic_runtime/agent/*` → `diagnostics/agent/*`
- `diagnostic_runtime/guardrails/*` → `diagnostics/guardrails/*`

**Test command:** `python -m pytest tests/test_diagnostic_agent_runner.py tests/test_diagnostic_agent_safety_check.py -q`

### R1-C7: application/diagnostic_contracts.py -> diagnostics/contracts/expected.py

**Move:**
- `application/diagnostic_contracts.py` → `diagnostics/contracts/expected.py`

**Update imports in:** `application/diagnostic_service.py`
**Test command:** `python -m pytest tests/test_stage42_diagnostic_contracts.py -q`

### R1-C8: diagnostic_runtime/analysis -> diagnostics/analysis

**Move:**
- `diagnostic_runtime/analysis/*` → `diagnostics/analysis/*`

**Update imports in:** `application/diagnostic_analysis_service.py`
**Test command:** `python -m pytest tests/test_stage44_diagnostic_analysis.py tests/test_stage44_diagnostic_analysis_service.py -q`

### R1-C9: sim/pybullet_diagnostics.py + sim/urdf_calibration.py -> diagnostics/geometry/

**Move:**
- `sim/pybullet_diagnostics.py` → `diagnostics/geometry/pybullet_diagnostics.py`
- `sim/urdf_calibration.py` → `diagnostics/geometry/urdf_calibration.py`

**Update imports in:** `cli/diagnose_backend_geometry.py`, `cli/calibrate_urdf_geometry.py`
**Test command:** `python -m pytest tests/test_stage2_*.py -q`

### R1-C10: Legacy Directory Cleanup

After all shims verify no caller depends on the old paths via `rg`:
- Delete `diagnostic_runtime/`
- Clean `reports/` shims
- Update `diagnostics/` to be the authoritative package

**Final audit:** `rg "from diagnostic_runtime|from reports\.evidence_manifest" -g "*.py"`

---

## 4. Dependency Rules

After migration, the `diagnostics/` package must follow these rules:

```text
diagnostics/ MAY import:
  - robot.safety.* (read safety result types)
  - perception.* (read observation types)
  - Standard library

diagnostics/ MUST NOT import:
  - application.*
  - cli.*
  - robot.runtime.* (must not call SafetyRuntime or RobotDeviceAdapter)
  - robot.adapters.*
  - runtime_db.* (read-only metrics queries go through application)
```

```text
application/ MAY import diagnostics.*
diagnostics/ MUST NOT import application.*
```

This matches the existing `robot/` → `application/` → `cli/` layering.

---

## 5. Test Strategy

Each sub-stage must be verified independently:

| Sub-stage | Test Command |
|---|---|
| R1-C1 | `rg "from diagnostic_runtime|from reports\.evidence_manifest" -g "*.py"` (baseline) |
| R1-C2 | `python -m pytest tests/test_stage37_agent_context_*.py -q` |
| R1-C3 | `python -m pytest tests/test_diagnostics_tools.py tests/test_diagnostics_report.py -q` |
| R1-C4 | `python -m pytest tests/test_evidence_manifest.py -q` |
| R1-C5 | `python -m pytest tests/test_diagnostic_runtime_runner.py tests/test_diagnostic_runtime_integration.py -q` |
| R1-C6 | `python -m pytest tests/test_diagnostic_agent_runner.py tests/test_diagnostic_agent_safety_check.py -q` |
| R1-C7 | `python -m pytest tests/test_stage42_diagnostic_contracts.py -q` |
| R1-C8 | `python -m pytest tests/test_stage44_diagnostic_analysis.py tests/test_stage44_diagnostic_analysis_service.py -q` |
| R1-C9 | `python -m pytest tests/test_stage2_*.py -q` |
| R1-C10 | `rg "from diagnostic_runtime|from reports\.evidence_manifest" -g "*.py"` (final audit) |

After the full migration, run the full diagnostic test suite:

```powershell
python -m pytest tests/test_diagnostic_cli.py tests/test_diagnostic_*.py tests/test_stage3?_*.py tests/test_stage4?_*.py -q
```

---

## 6. Risk Assessment

| Risk | Mitigation |
|---|---|
| Import path changes break existing tests | Shim packages keep old paths working |
| `application/diagnostic_service.py` has mixed responsibilities | Split orchestration logic stays in `application/`, domain logic moves to `diagnostics/` |
| `reports/` still has non-evidence files | Not part of migration — `reports/` keeps `runtime_*.py`, `backend_comparison.py`, `plot_3d.py` |
| `sim/` geometry tools differ from diagnostics | They are diagnostic geometry tools, so they belong under `diagnostics/geometry/` |
| Large diff makes review hard | Each sub-stage is one commit with focused tests |
