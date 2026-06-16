from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import DiagnosticRuntimeResult


def write_runtime_trace(result: DiagnosticRuntimeResult) -> Path:
    """Write a structured trace JSON for a diagnostic runtime run.

    The trace records:
    - timestamp
    - input context path
    - deterministic report path
    - agent report path (if run)
    - safety violations
    - diagnostic runtime schema version
    """
    trace: dict[str, Any] = {
        "schema_version": "diagnostic_runtime_trace.v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_context_path": str(result.context_path),
        "deterministic_report_path": str(result.deterministic_report_path),
        "agent_report_path": str(result.agent_report_path) if result.agent_report_path else None,
        "safety_violations": list(result.safety_violations),
        "has_violations": len(result.safety_violations) > 0,
    }

    trace_path = result.trace_path
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace_path.write_text(json.dumps(trace, indent=2, ensure_ascii=False), encoding="utf-8")
    return trace_path
