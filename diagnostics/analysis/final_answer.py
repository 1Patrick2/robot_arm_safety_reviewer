from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LLMFinalAnswer:
    """Structured final answer from an LLM diagnostic analysis.

    This is advisory only — it must not approve, reject, modify, or execute
    robot actions. The deterministic safety decision is authoritative.
    """

    schema_version: str = "llm_final_answer.v1"
    provider: str = "fake"
    model: str = "fake"
    advisory_decision: str = "manual_review"
    risk_level: str = "medium"
    short_answer: str = ""
    reasoning_summary: str = ""
    evidence_refs: tuple[str, ...] = ()
    limitations: tuple[str, ...] = (
        "LLM output is advisory only. Not used to execute robot actions.",
    )

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
    """Deterministic fake LLM final answer for testing.

    Does not call any external API. Only uses deterministic evidence.
    """
    advisory_map = {
        "approve": "approve",
        "manual_review": "manual_review",
        "reject": "reject",
    }
    adv = advisory_map.get(fused_decision, "manual_review")
    return LLMFinalAnswer(
        advisory_decision=adv,
        risk_level=fused_risk_level,
        short_answer=f"Advisory: {adv} based on deterministic evidence.",
        reasoning_summary=(
            f"The deterministic safety pipeline evaluated trajectory "
            f"'{dataset_name}' and produced a fused decision of "
            f"'{fused_decision}'."
        ),
        evidence_refs=(
            "summary.perception_fused_decision",
            "summary.external_dataset_name",
            "artifacts.evidence_manifest",
        ),
    )


def write_final_answer(answer: LLMFinalAnswer, output_path: Path) -> Path:
    """Write an ``LLMFinalAnswer`` to a JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(answer.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return output_path
