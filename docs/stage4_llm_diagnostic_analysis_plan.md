# Stage 4: Evidence-Driven LLM Diagnostic Analysis Plan

> **Status:** Planning document for Stage 4 (not yet implemented).  
> **Stage 3** delivered a deterministic diagnostic pipeline (completed).  
> **Stage 4** upgrades it to evidence-driven LLM diagnostic analysis.

## 1. Problem Statement

Stage 3 built a complete deterministic diagnostic pipeline: `SafetyRuntime` → episode recording → visual sandbox artifacts → runtime metrics DB → diagnostic context → deterministic report → optional diagnostic agent with guardrails → evidence manifest → diagnostic regression.

**What Stage 3 proved:** pipeline correctness (each step runs deterministically) and evidence completeness (all key artifacts are generated and indexed).

**What Stage 3 has not fully proven:** answer correctness under complex scenarios (Level-1 benchmarks use single-obstacle, obvious approve/reject cases only) and LLM-driven evidence analysis (the optional agent operates on a simple prompt with no structured evidence grouping or contract validation).

## 2. Stage 4 Goal

```
Stage 4: Level-2 Safety Scenarios + Evidence-Driven LLM Diagnostic Analysis
```

Stage 4 evolves the project from a deterministic diagnostic pipeline into an evidence-driven robot safety diagnostic framework. The core addition is a structured analysis layer that consumes grouped evidence, compares actual outcomes against expected contracts, and produces structured diagnostic findings — without modifying the deterministic safety boundary.

## 3. Non-Goals

```
- LLM must not control robot motion.
- LLM must not plan trajectories.
- LLM must not approve, reject, or override safety decisions.
- LLM must not modify policy actions.
- LLM must not call RobotDeviceAdapter or any execution path.
- LLM analysis is advisory and diagnostic-only.
```

These boundaries must remain enforced by architecture: diagnostic components should not access `RobotDeviceAdapter`, `SafetyRuntime`, or any execution path.

## 4. External Project Lessons

*Note: these projects are used as conceptual references only; Stage 4 does not attempt to reproduce their full benchmark scale or robot-control assumptions.*

- **SafeAgentBench** (arXiv: 2412.13178): hazard-oriented benchmark design — safety evaluation must cover near-threshold and ambiguous cases, not just obvious collisions or task success rates.
- **PARTNR** (arXiv: 2411.00081): complex embodied tasks need spatial/temporal constraint handling and simulation-in-the-loop validation for task generation.
- **SMART-LLM** (arXiv: 2309.10062): multi-agent role decomposition — specialized agents for different analysis dimensions, all diagnostic-only.
- **Safe-BeAl / SafePlan-Bench** (arXiv: 2504.14650): even without malicious input, embodied LLM agents can produce unsafe behavior; safety evaluation must test near-threshold and ambiguous scenarios.

## 5. Level-2 Scenario Taxonomy

**Level-1 (Stage 3):** single obvious obstacle, simple approve/reject, pipeline smoke-testing.

**Level-2 (Stage 4 target):** requires trajectory-level reasoning and `min_clearance` / `worst_step` / `closest_obstacle` evidence; may include multiple obstacles and mixed decisions in one sequence; requires expected contract for validation.

### Proposed Level-2 Cases

| Case ID | Purpose | Expected Safety Behavior | Key Evidence Required |
|---|---|---|---|
| `midpoint_collision_sequence` | Collision occurs mid-trajectory, not at endpoint | Reject at midpoint; earlier steps may approve | `min_clearance`, `worst_sequence_step_index`, `trajectory_overview_data` |
| `near_threshold_clearance_sequence` | Clearance hovers near threshold across multiple steps | Manual review for borderline steps; mixed decisions | `min_clearance`, `closest_robot_link`, `closest_obstacle`, `clearance_curve` |
| `mixed_decision_sequence` | Sequence contains approve, manual_review, and reject steps | Each step correctly classified; reject does not execute | `decision` per step, `blocked_reason`, `evidence_manifest` |
| `multi_obstacle_attribution_sequence` | Two obstacles at different distances; closest attribution matters | Closest obstacle correctly identified per step | `closest_obstacle`, `closest_robot_link`, `trajectory_overview_data` |
| `joint_limit_plus_obstacle_sequence` | Both joint limit violation and obstacle collision present | Reject with both violation types recorded | `violations`, `min_clearance`, `joint_limits` |

---

## 6. Expected Contract Design

An expected contract defines what a correct safety outcome looks like for a given test case. This moves validation from "did the pipeline run" to "was the answer correct."

```json
{
  "case_id": "near_threshold_clearance_sequence",
  "expected": {
    "total_steps": 3,
    "min_approved_steps": 1,
    "min_manual_review_steps": 1,
    "min_rejected_steps": 0,
    "expected_final_status": "manual_review",
    "required_artifacts": [
      "diagnostic_context_json", "deterministic_report",
      "diagnostic_runtime_trace", "trajectory_overview",
      "trajectory_overview_data", "evidence_manifest"
    ]
  }
}
```

The contract constrains both structural completeness (required artifacts exist) and semantic correctness (expected decisions and clearance bands).

## 7. Evidence Group Schema

Evidence groups organize evidence by analytical perspective.

```json
{
  "evidence_groups": {
    "runtime": ["metadata", "steps"],
    "safety": ["decision", "risk_level", "violations", "blocked_reason"],
    "geometry": ["min_clearance", "worst_sequence_step_index", "backend_worst_step", "closest_robot_link", "closest_obstacle"],
    "visual": ["clearance_curve", "trajectory_overview"],
    "structured_visual": ["trajectory_overview_data"],
    "diagnostic": ["diagnostic_context_json", "diagnostic_context_markdown", "deterministic_report", "diagnostic_runtime_trace"],
    "regression": ["regression_summary"],
    "agent": ["diagnostic_agent_report"]
  }
}
```

Purpose: each analyst role receives only its relevant evidence group, reducing noise and making evidence references traceable.

## 8. Expected-vs-Actual Regression

```
pipeline_passed:   code path ran without fatal error.
evidence_complete: required evidence artifacts exist and are indexed.
contract_passed:   actual safety outcome matches expected contract.
```

```json
{
  "case_id": "mixed_decision_sequence",
  "pipeline_passed": true, "evidence_complete": true, "contract_passed": true,
  "actual": {
    "total_steps": 4, "approved_steps": 2, "manual_review_steps": 1,
    "rejected_steps": 1, "min_clearance": -0.02, "closest_obstacle": "obs_2"
  },
  "expected": {
    "min_approved_steps": 1, "min_manual_review_steps": 1, "min_rejected_steps": 1
  },
  "errors": []
}
```

## 9. LLM Diagnostic Analyst Design

**Inputs:** `diagnostic_context.json`, `evidence_manifest.json`, `diagnostic_runtime_trace.json`, `trajectory_overview_data.json`, `deterministic_report.md`, expected-vs-actual regression result.

**Output Schema:**

```json
{
  "schema_version": "llm_diagnostic_analysis.v1",
  "case_id": "near_threshold_clearance_sequence",
  "risk_summary": "The sequence contains a near-threshold clearance event at step 2.",
  "root_cause_hypotheses": [
    {
      "hypothesis": "Minimum clearance occurs between link_3 and obstacle obs_1.",
      "evidence_refs": [
        "diagnostic_context.summary.min_clearance",
        "diagnostic_context.summary.closest_robot_link",
        "diagnostic_context.summary.closest_obstacle",
        "trajectory_overview_data.steps[1]"
      ],
      "confidence": "medium"
    }
  ],
  "evidence_used": ["diagnostic_context_json", "trajectory_overview_data", "deterministic_report", "evidence_manifest"],
  "uncertainties": ["The analysis uses structured visual data, not raw image understanding."],
  "prohibited_actions_detected": []
}
```

**Guardrails:**
- Planned enforcement: the application layer should validate LLM output against a structured schema and reject free-form or schema-invalid responses.
- Each finding must include `evidence_refs` to specific evidence fields.
- `uncertainties` is required — analyst must state what it does not know.
- Planned: extend `check_agent_report` to validate that no prohibited patterns appear in the output.

## 10. Multi-Agent Diagnostic Roadmap

Multi-agent analysis is a late Stage 4 extension, planned after the single-agent diagnostic analyst has been validated.

| Role | Responsibility | Input Evidence Group |
|---|---|---|
| `SafetyRuleAnalyst` | Check joint limits, violations, risk classification | `safety`, `runtime` |
| `GeometryAnalyst` | Analyze clearance, closest link/obstacle attribution | `geometry`, `structured_visual` |
| `VisualEvidenceAnalyst` | Summarize visual evidence patterns | `visual`, `structured_visual` |
| `RegressionAnalyst` | Compare actual vs expected, flag gaps | `regression`, `diagnostic` |
| `DiagnosticSynthesizer` | Merge findings, produce final report | All groups |

All agents are diagnostic-only.

## 11. Implementation Roadmap

**Stage 4.1:** Planning and Architecture Boundary. Define Stage 4 scope, non-goals, Level-2 scenario taxonomy, evidence group schema, and LLM diagnostic analyst boundary. (This document.)
**Stage 4.2:** Level-2 Scenarios + Contracts. Create scene files and action sequences; define expected contract JSONs; update regression runner.
**Stage 4.3:** Evidence Groups + Expected-vs-Actual. Implement evidence groups in manifest; extend regression to three-level pass/fail; add contract validation and CLI output.
**Stage 4.4:** LLM Diagnostic Analyst. Implement analyst with structured JSON output; wire evidence groups; add guardrails; implement provider adapter (fake + one real). Multi-agent orchestration is deferred until after the single-agent analyst is validated.

## 12. Acceptance Criteria

```
- Level-2 benchmark cases exist and produce expected safety outcomes.
- Expected contracts validate answer correctness (not just pipeline completion).
- Evidence manifest supports evidence groups with structured grouping.
- Regression distinguishes pipeline_passed / evidence_complete / contract_passed.
- LLM diagnostic analyst outputs structured findings with evidence references, uncertainties, and confidence levels.
- Guardrails prevent LLM from acting as a safety decision maker.
- No LLM control path is introduced anywhere in the system.
```
