# Real Integrated Demo

## Overview

The integrated demo chains the full project pipeline:

```
External trajectory input
  → SafetyRuntime evaluation
  → Optional YOLO/ONNX perception
  → Perception safety fusion
  → Evidence manifest
  → Optional LLM diagnostic answer
  → final_answer.md
```

## Command

```powershell
PYTHONPATH=. python tools/run_real_integrated_demo.py ^
  --episode bench/external_trajectory_smoke/lerobot_style_episode.json ^
  --mapping bench/external_trajectory_smoke/mapping_config.json ^
  --scene bench/external_trajectory_smoke/scene.json ^
  --yolo-model local_data/real_perception_smoke/yolo26n.onnx ^
  --image local_data/real_perception_smoke/bus.jpg ^
  --llm-provider fake ^
  --out artifacts/real_integrated_demo
```

## Outputs

| File | Description |
|---|---|
| `converted_sequence.json` | External trajectory → PolicyActionSequence |
| `external_trajectory_record.json` | Dataset metadata and mapping config |
| `diagnostic_context.json` | Episode summary from SafetyRuntime |
| `perception_inference_record.json` | YOLO detection + fusion result |
| `evidence_manifest.json` | Full evidence index with all groups |
| `llm_diagnostic_analysis.json` | LLM advisory answer |
| `final_answer.md` | Deterministic + advisory combined result |
| `summary.md` | Quick overview |

## Interpreting final_answer.md

- **Deterministic Safety Result**: authoritative — this is what the system executes.
- **LLM Advisory Answer**: informational only — not used to control the robot.
- **Boundary statement**: always present to clarify LLM ≠ safety decision.
