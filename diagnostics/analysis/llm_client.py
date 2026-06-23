"""Real OpenAI-compatible LLM adapter for diagnostic analysis.

Requires ``DEEPSEEK_API_KEY`` or ``OPENAI_API_KEY`` environment variable.
Lazy-imports ``httpx`` only when ``infer()`` is called.
"""

from __future__ import annotations

import os
from typing import Any

from diagnostics.analysis.final_answer import LLMFinalAnswer


def call_llm_diagnostic_analysis(
    *,
    provider: str = "deepseek",
    model: str = "",
    context: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    external_trajectory_record: dict[str, Any] | None = None,
    perception_record: dict[str, Any] | None = None,
) -> LLMFinalAnswer:
    """Call a real LLM API for diagnostic analysis.

    Args:
        provider: ``"deepseek"`` or ``"openai-compatible"``.
        model: Model name (e.g. ``"deepseek-chat"``, ``"gpt-4o-mini"``).
        context: Diagnostic context dict.
        manifest: Evidence manifest dict.
        external_trajectory_record: External trajectory record dict.
        perception_record: Perception inference record dict.

    Returns:
        An ``LLMFinalAnswer`` with the LLM's advisory analysis.

    Raises:
        RuntimeError: If the required API key is missing or the API call fails.
    """
    if provider == "deepseek":
        api_key = os.environ.get("DEEPSEEK_API_KEY")
        base_url = os.environ.get("OPENAI_COMPATIBLE_BASE_URL", "https://api.deepseek.com")
        if not model:
            model = "deepseek-chat"
    elif provider == "openai-compatible":
        api_key = os.environ.get("OPENAI_API_KEY")
        base_url = os.environ.get("OPENAI_COMPATIBLE_BASE_URL", "https://api.openai.com/v1")
        if not model:
            model = "gpt-4o-mini"
    else:
        raise ValueError(f"unsupported LLM provider: '{provider}'")

    if not api_key:
        raise RuntimeError(
            f"{provider} requires API key via environment variable "
            f"({'DEEPSEEK_API_KEY' if provider == 'deepseek' else 'OPENAI_API_KEY'})"
        )

    # Build structured prompt from evidence
    prompt = _build_diagnostic_prompt(
        context=context, manifest=manifest,
        external_trajectory_record=external_trajectory_record,
        perception_record=perception_record,
    )

    # Call API
    try:
        import httpx  # noqa: PLC0415
    except ImportError:
        raise RuntimeError("httpx is required for real LLM calls. Install with: pip install httpx")

    resp = httpx.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 2048,
            "temperature": 0.0,
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    content = data["choices"][0]["message"]["content"]

    # Parse JSON from LLM response
    import json  # noqa: PLC0415
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {"advisory_decision": "unknown", "risk_level": "unknown",
                  "short_answer": content[:500], "reasoning_summary": content[:1000]}

    return LLMFinalAnswer(
        provider=provider,
        model=model,
        advisory_decision=result.get("advisory_decision", "unknown"),
        risk_level=result.get("risk_level", "unknown"),
        short_answer=result.get("short_answer", ""),
        reasoning_summary=result.get("reasoning_summary", ""),
        evidence_refs=tuple(result.get("evidence_refs", [])),
    )


_SYSTEM_PROMPT = """You are a diagnostic analysis assistant for a robot arm safety evaluation framework.
You receive structured diagnostic evidence and must output a JSON analysis.
You must not claim to approve, reject, or execute robot actions.
Output format:
{
  "advisory_decision": "approve" | "manual_review" | "reject" | "unknown",
  "risk_level": "low" | "medium" | "high" | "unknown",
  "short_answer": "one-sentence summary",
  "reasoning_summary": "2-3 sentence explanation",
  "evidence_refs": ["dot.path.ref1", "dot.path.ref2"]
}"""


def _build_diagnostic_prompt(
    context: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    external_trajectory_record: dict[str, Any] | None = None,
    perception_record: dict[str, Any] | None = None,
) -> str:
    """Build a structured prompt from diagnostic evidence."""
    lines = ["## Diagnostic Context"]
    if context:
        lines.append(f"- Episode: {context.get('episode_id', '?')}")
        lines.append(f"- Total steps: {context.get('total_steps', '?')}")
        lines.append(f"- Approved: {context.get('approved_steps', '?')}")
        lines.append(f"- Rejected: {context.get('rejected_steps', '?')}")

    if external_trajectory_record:
        lines.append(f"\n## External Trajectory")
        lines.append(f"- Dataset: {external_trajectory_record.get('dataset_name', '?')}")
        lines.append(f"- Frames: {external_trajectory_record.get('frame_count', '?')}")

    if perception_record:
        fusion = perception_record.get("fusion_result", {})
        lines.append(f"\n## Perception Fusion")
        lines.append(f"- Fused decision: {fusion.get('fused_decision', '?')}")
        lines.append(f"- Risk level: {fusion.get('fused_risk_level', '?')}")

    if manifest:
        checks = manifest.get("checks", {})
        groups = manifest.get("evidence_groups", {})
        available = [k for k, v in groups.items() if v.get("available")]
        lines.append(f"\n## Evidence Manifest")
        lines.append(f"- Checks: {json.dumps(checks)}")
        lines.append(f"- Available groups: {available}")

    lines.append("\nProvide your advisory analysis in JSON format.")
    return "\n".join(lines)


import json  # noqa: E402
