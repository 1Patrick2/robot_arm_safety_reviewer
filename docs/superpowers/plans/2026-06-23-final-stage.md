# Stage 6.3 Real Integrated Demo and Test Suite Consolidation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the project with a real input-to-output integrated demo, consolidate the test suite from stage-based files into capability-level tests, add CI, and document the final testing strategy.

**Architecture:** Four sequential commits: (1) integrated demo runner + LLM final answer schema, (2) 6 capability-level test files replacing ~15 stage-based tests, (3) GitHub Actions CI workflow, (4) documentation and testing strategy.

**Tech Stack:** Python 3.10+, pytest, GitHub Actions, existing application services.

## Global Constraints

- LLM advisory output is allowed but must not approve/reject/execute robot actions.
- Deterministic SafetyRuntime and fusion remain the source of execution safety.
- Core CI tests must not require network, model weights, API keys, or heavy optional dependencies.
- Real YOLO, LeRobot Hub, and real LLM are manual smoke only.
- No new production features — only demo tooling and test reorganization.
- Old stage-based tests are removed only after new capability tests cover their assertions.

---

## Files Overview

| File | Action | Purpose |
|---|---|---|
| `diagnostics/analysis/final_answer.py` | Create | LLM final answer schema + fake generator |
| `tools/run_real_integrated_demo.py` | Create | End-to-end demo runner (trajectory → safety → YOLO → LLM → answer) |
| `tests/test_safety_pipeline.py` | Create | Capability test for robot safety pipeline |
| `tests/test_diagnostics_evidence_pipeline.py` | Create | Capability test for diagnostics + evidence |
| `tests/test_perception_pipeline.py` | Create | Capability test for perception pipeline |
| `tests/test_external_trajectory_pipeline.py` | Create | Capability test for external trajectory |
| `tests/test_integrated_demo_pipeline.py` | Create | Capability test for fake integrated demo |
| `tests/test_import_boundaries.py` | Create | Import boundary and safety boundary tests |
| `tests/manual/test_real_llm_diagnostic_smoke.py` | Create | Manual real LLM smoke test |
| `tests/manual/test_real_integrated_demo.py` | Create | Manual real integrated demo smoke test |
| `.github/workflows/core-tests.yml` | Create | GitHub Actions CI workflow |
| `docs/testing_strategy.md` | Create | Testing strategy documentation |
| `docs/real_integrated_demo.md` | Create | Integrated demo documentation |
| `docs/project_current_status.md` | Modify | Update status |
| `docs/final_validation.md` | Modify | Update validation docs |
| `README.md` | Modify | Update demo section |
| `main_prompt.md` | Modify | Update handoff prompt |

---

### Task 1: Add LLM final answer schema and fake generator

**Files:**
- Create: `diagnostics/analysis/final_answer.py`

**Interfaces:**
- Produces: `LLMFinalAnswer` dataclass, `generate_fake_final_answer()` function

- [ ] **Step 1: Create `diagnostics/analysis/final_answer.py`**

```python
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LLMFinalAnswer:
    schema_version: str = "llm_final_answer.v1"
    provider: str = "fake"
    model: str = "fake"
    advisory_decision: str = "manual_review"
    risk_level: str = "medium"
    short_answer: str = ""
    reasoning_summary: str = ""
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ("LLM output is advisory only. Not used to execute robot actions.",)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "provider": self.provider,
            "model": self.model,
            "advisory_decision": self.advisory_decision,
            "risk_level": self.risk_level,
            "short_answer": self.short_answer,
            "reasoning_summary": self.reasoning_summary,
            "evidence_refs": list(self.evidence_refs),
            "limitations": list(self.limitations),
        }


def generate_fake_final_answer(
    *,
    fused_decision: str = "manual_review",
    fused_risk_level: str = "medium",
    dataset_name: str = "unknown",
) -> LLMFinalAnswer:
    """Deterministic fake LLM final answer for testing."""
    advisory_map = {"approve": "approve", "manual_review": "manual_review", "reject": "reject"}
    adv = advisory_map.get(fused_decision, "manual_review")
    return LLMFinalAnswer(
        advisory_decision=adv,
        risk_level=fused_risk_level,
        short_answer=f"Advisory: {adv} based on deterministic evidence.",
        reasoning_summary=f"The deterministic safety pipeline evaluated trajectory '{dataset_name}' "
                         f"and produced a fused decision of '{fused_decision}'.",
        evidence_refs=(
            "summary.perception_fused_decision",
            "summary.external_dataset_name",
            "artifacts.evidence_manifest",
        ),
    )


def write_final_answer(answer: LLMFinalAnswer, output_path: Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(answer.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
    return output_path
```

- [ ] **Step 2: Run test to verify it works**

```python
# Inline test
from diagnostics.analysis.final_answer import LLMFinalAnswer, generate_fake_final_answer
ans = generate_fake_final_answer(fused_decision="reject")
assert ans.advisory_decision == "reject"
assert "advisory only" in ans.limitations[0]
```

- [ ] **Step 3: Commit**

```bash
git add diagnostics/analysis/final_answer.py
git commit -m "feat: add LLM final answer schema"
```

---

### Task 2: Add integrated demo runner

**Files:**
- Create: `tools/run_real_integrated_demo.py`

**Interfaces:**
- Consumes: `bench/adapters/*`, `diagnostics/analysis/final_answer.py`, `application/sandbox_service`, `diagnostics/evidence/*`
- Produces: demo runner CLI

- [ ] **Step 1: Create `tools/run_real_integrated_demo.py`**

Key logic:
1. Parse CLI args (--episode, --mapping, --scene, --yolo-model, --image, --llm-provider, --out, etc.)
2. Load episode → convert to PolicyActionSequence → run sandbox
3. If YOLO not skipped: run UltralyticsYoloAdapter → perception_inference_record
4. Build evidence_manifest with external_trajectory + perception records
5. If LLM not skipped: call real/fake LLM → write llm_diagnostic_analysis.json
6. Write final_answer.md and summary.md

See interact.md Part 4 for full spec of CLI args and outputs.

- [ ] **Step 2: Run smoke test with fake LLM**

```bash
PYTHONPATH=. python tools/run_real_integrated_demo.py \
  --episode bench/external_trajectory_smoke/lerobot_style_episode.json \
  --mapping bench/external_trajectory_smoke/mapping_config.json \
  --scene bench/external_trajectory_smoke/scene.json \
  --llm-provider fake \
  --out /tmp/integrated_demo
```

- [ ] **Step 3: Commit**

```bash
git add tools/run_real_integrated_demo.py
git commit -m "feat: add real integrated demo runner"
```

---

### Task 3: Create test_safety_pipeline.py

**Files:**
- Create: `tests/test_safety_pipeline.py`
- Delete later (after all cap tests pass): `tests/test_stage1_*.py`, `tests/test_stage2_*.py`, `tests/test_stage3_*.py` (partial)

- [ ] **Step 1: Create capability test with key assertions from old stage tests**

Cover:
- Scene + sequence → run_sandbox → approve/manual_review/reject
- Basic backend_factory create_backend works
- SafetyRuntime step with known approve case
- Episode recording produces metadata.json + steps.jsonl

- [ ] **Step 2: Run to verify**

```bash
python -m pytest tests/test_safety_pipeline.py -q
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_safety_pipeline.py
git commit -m "test: add consolidated safety pipeline test"
```

---

### Task 4: Create test_diagnostics_evidence_pipeline.py

**Files:**
- Create: `tests/test_diagnostics_evidence_pipeline.py`

- [ ] **Step 1: Create capability test covering evidence_manifest, expected_contract, evidence_groups**

Cover:
- build_evidence_manifest with context + report + trace
- validate_expected_contract pass/fail
- evidence_groups structure
- required_artifacts and required_evidence_groups

- [ ] **Step 2: Run to verify**

```bash
python -m pytest tests/test_diagnostics_evidence_pipeline.py -q
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_diagnostics_evidence_pipeline.py
git commit -m "test: add consolidated diagnostics evidence test"
```

---

### Task 5: Create test_perception_pipeline.py

**Files:**
- Create: `tests/test_perception_pipeline.py`

- [ ] **Step 1: Create capability test covering perception schema, adapter, fusion, evidence**

Cover:
- PerceptionResult schema (load_perception_result valid/invalid)
- FakePerceptionModelAdapter returns valid result
- build_safety_observations → human_in_danger_zone
- fuse_safety_with_perception → reject
- PerceptionInferenceRecord written and manifest integrated

- [ ] **Step 2: Run to verify**

```bash
python -m pytest tests/test_perception_pipeline.py -q
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_perception_pipeline.py
git commit -m "test: add consolidated perception pipeline test"
```

---

### Task 6: Create test_external_trajectory_pipeline.py

**Files:**
- Create: `tests/test_external_trajectory_pipeline.py`

- [ ] **Step 1: Create capability test covering external trajectory end-to-end**

Cover:
- ExternalTrajectory / ExternalActionFrame / ActionMappingConfig creation
- load_lerobot_style_episode valid/invalid
- external_trajectory_to_policy_sequence conversion
- ExternalTrajectoryRecord write
- evidence_manifest external_trajectory group
- expected_contract with external_trajectory

- [ ] **Step 2: Run to verify**

```bash
python -m pytest tests/test_external_trajectory_pipeline.py -q
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_external_trajectory_pipeline.py
git commit -m "test: add consolidated external trajectory test"
```

---

### Task 7: Create test_integrated_demo_pipeline.py

**Files:**
- Create: `tests/test_integrated_demo_pipeline.py`

- [ ] **Step 1: Create capability test covering fake integrated demo**

Cover:
- external trajectory → safety runtime → approve
- fake perception → fusion (human_in_danger_zone → reject)
- build evidence_manifest with both records
- generate fake LLM final answer
- write final_answer.json
- validate expected contract

- [ ] **Step 2: Run to verify**

```bash
python -m pytest tests/test_integrated_demo_pipeline.py -q
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_integrated_demo_pipeline.py
git commit -m "test: add consolidated integrated demo test"
```

---

### Task 8: Create test_import_boundaries.py

**Files:**
- Create: `tests/test_import_boundaries.py`

- [ ] **Step 1: Create boundary tests**

Cover:
- No legacy imports (dataset_adapters, gateway, runtime_db, reports, sim)
- No robot_safety/robot_runtime/robots imports
- lerobot import only in optional adapter
- ultralytics import only lazy inside adapter
- LLM does not appear in safety decision path

- [ ] **Step 2: Run to verify**

```bash
python -m pytest tests/test_import_boundaries.py -q
```

- [ ] **Step 3: Commit**

```bash
git add tests/test_import_boundaries.py
git commit -m "test: add import boundary tests"
```

---

### Task 9: Remove redundant stage-based tests

**Files:**
- Delete: `tests/test_stage51_*.py`, `tests/test_stage52_*.py`, `tests/test_stage53_*.py`, `tests/test_stage54_*.py`, `tests/test_stage61_*.py`
- Keep: `tests/manual/*`, `tests/test_evidence_manifest.py`, `tests/test_diagnostic_*.py`, `tests/test_r1_*`, `tests/test_stage42_*`

- [ ] **Step 1: Verify new cap tests cover old assertions**

```bash
python -m pytest tests/test_safety_pipeline.py tests/test_diagnostics_evidence_pipeline.py tests/test_perception_pipeline.py tests/test_external_trajectory_pipeline.py tests/test_integrated_demo_pipeline.py tests/test_import_boundaries.py -q
```

- [ ] **Step 2: Run existing full suite to confirm coverage**

```bash
python -m pytest -q
```

- [ ] **Step 3: Commit**

```bash
git add -A
git commit -m "test: remove redundant stage-based tests after consolidation"
```

---

### Task 10: Add GitHub Actions CI workflow

**Files:**
- Create: `.github/workflows/core-tests.yml`

- [ ] **Step 1: Create CI workflow**

```yaml
name: Core Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: |
          python -m pytest \
            tests/test_safety_pipeline.py \
            tests/test_diagnostics_evidence_pipeline.py \
            tests/test_perception_pipeline.py \
            tests/test_external_trajectory_pipeline.py \
            tests/test_integrated_demo_pipeline.py \
            tests/test_import_boundaries.py \
            -q
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/core-tests.yml
git commit -m "ci: add core test workflow"
```

---

### Task 11: Documentation

**Files:**
- Create: `docs/testing_strategy.md`, `docs/real_integrated_demo.md`
- Modify: `docs/project_current_status.md`, `docs/final_validation.md`, `README.md`, `main_prompt.md`

- [ ] **Step 1: Create docs/testing_strategy.md** — explain 3-layer test structure
- [ ] **Step 2: Create docs/real_integrated_demo.md** — demo command + output format
- [ ] **Step 3: Update docs/project_current_status.md** — add v0.2 status
- [ ] **Step 4: Update docs/final_validation.md** — add new CI/validation commands
- [ ] **Step 5: Update README.md** — add demo section
- [ ] **Step 6: Update main_prompt.md** — final status
- [ ] **Step 7: Commit**

```bash
git add docs/ README.md main_prompt.md
git commit -m "docs: document real integrated demo and testing strategy"
```

---

## Verification

```bash
# Run all 6 capability tests
python -m pytest tests/test_safety_pipeline.py tests/test_diagnostics_evidence_pipeline.py tests/test_perception_pipeline.py tests/test_external_trajectory_pipeline.py tests/test_integrated_demo_pipeline.py tests/test_import_boundaries.py -q

# Run external trajectory smoke
PYTHONPATH=. python tools/run_external_trajectory_smoke.py --episode bench/external_trajectory_smoke/lerobot_style_episode.json --mapping bench/external_trajectory_smoke/mapping_config.json --scene bench/external_trajectory_smoke/scene.json --expected-contract bench/external_trajectory_smoke/expected_contract.json --out /tmp/ext_smoke

# Run integrated demo with fake LLM
PYTHONPATH=. python tools/run_real_integrated_demo.py --episode bench/external_trajectory_smoke/lerobot_style_episode.json --mapping bench/external_trajectory_smoke/mapping_config.json --scene bench/external_trajectory_smoke/scene.json --llm-provider fake --out /tmp/int_demo

# Audit
rg "from dataset_adapters|from gateway|from runtime_db|from reports|from sim|robot_safety|robot_runtime|from robots" -g "*.py" .
```
