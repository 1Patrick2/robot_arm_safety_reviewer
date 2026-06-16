from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .deepseek_adapter import run_deepseek_agent
from .fake_adapter import run_fake_agent


def run_diagnostic_agent(
    context_path: str | Path,
    output_dir: str | Path,
    provider: str = "fake",
) -> dict[str, Any]:
    """Run a diagnostic agent on a diagnostic_context.json file.

    Args:
        context_path: Path to diagnostic_context.json.
        output_dir: Directory to write the report to.
        provider: "fake" (default) or "deepseek".

    Returns:
        Dict with keys: provider, report_path.

    Raises:
        FileNotFoundError: If the context file does not exist.
        ValueError: If the provider is unsupported.
    """
    context_path = Path(context_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not context_path.exists():
        raise FileNotFoundError(f"context not found: {context_path}")

    context = json.loads(context_path.read_text(encoding="utf-8"))

    if provider == "fake":
        report = run_fake_agent(context)
    elif provider == "deepseek":
        raise NotImplementedError("DeepSeek adapter not yet connected")
    else:
        raise ValueError(f"unsupported provider: {provider}")

    report_path = output_dir / "diagnostic_agent_report.md"
    report_path.write_text(report, encoding="utf-8")

    return {
        "provider": provider,
        "report_path": str(report_path),
    }
