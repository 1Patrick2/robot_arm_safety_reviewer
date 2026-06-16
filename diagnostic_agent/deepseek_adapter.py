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

    context_summary = (
        f"Episode {context.get('episode_id', 'unknown')}: "
        f"{context.get('total_steps', 0)} steps, "
        f"{context.get('approved_steps', 0)} approved, "
        f"{context.get('rejected_steps', 0)} rejected, "
        f"{context.get('blocked_steps', 0)} blocked, "
        f"min clearance {context.get('min_clearance', 'N/A')}."
    )

    critical_steps = context.get("critical_steps", [])
    artifacts = context.get("artifacts", [])

    user_prompt = (
        f"Analyze this diagnostic context and produce a safety report:\n\n"
        f"{context_summary}\n\n"
        f"Critical steps: {critical_steps}\n"
        f"Artifacts: {artifacts}"
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
