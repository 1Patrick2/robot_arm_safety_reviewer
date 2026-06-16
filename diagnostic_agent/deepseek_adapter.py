from __future__ import annotations

import os
from typing import Any

from .prompt import SYSTEM_PROMPT


def run_deepseek_agent(context: dict[str, Any]) -> str:
    """Call DeepSeek API and return a diagnostic report.

    Requires the DEEPSEEK_API_KEY environment variable.
    Uses the chat/completions endpoint with a strict diagnostic-only system prompt.

    Raises:
        RuntimeError: If DEEPSEEK_API_KEY is not set.
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY environment variable is not set")

    import httpx  # noqa: PLC0415
    import json  # noqa: PLC0415

    # Pass the full context as JSON so the LLM has all safety evidence.
    # This includes episode_id, sequence_id, backend, device, total_steps,
    # approved/executed/blocked/rejected/manual_review counts, min_clearance,
    # worst_sequence_step_index, backend_worst_step, closest_robot_link,
    # closest_obstacle, critical_steps (with full safety_result), artifacts,
    # and limitations.
    context_json = json.dumps(context, indent=2, ensure_ascii=False)

    user_prompt = (
        "Analyze the following diagnostic context and produce a safety report.\n\n"
        f"```json\n{context_json}\n```\n\n"
        "Focus on: safety summary, worst step analysis, critical steps, "
        "and artifact references. "
        "Cite specific evidence from the context. "
        "Do not speculate beyond the provided data."
    )

    response = httpx.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": 2048,
            "temperature": 0.0,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]
