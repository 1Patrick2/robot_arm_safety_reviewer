from __future__ import annotations

import re
from typing import Any

# Patterns that a diagnostic-only LLM must never produce.
# These are checked after every agent run (both fake and DeepSeek).
FORBIDDEN_PATTERNS: list[str] = [
    "approve this action",
    "safe to execute",
    "execute the action",
    "modify the target joints",
    "override the safety decision",
]


def check_agent_report(report: str, context: dict[str, Any] | None = None) -> list[str]:
    """Check an agent-generated report for forbidden patterns.

    Returns a list of matched forbidden patterns (empty = pass).
    The check is case-insensitive.
    """
    report_lower = report.lower()
    violations: list[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(re.escape(pattern), report_lower):
            violations.append(pattern)
    return violations


def check_agent_report_or_raise(report: str, context: dict[str, Any] | None = None) -> None:
    """Like *check_agent_report* but raises ``ValueError`` on violations."""
    violations = check_agent_report(report, context)
    if violations:
        raise ValueError(
            f"Agent report contains {len(violations)} forbidden pattern(s): "
            f"{violations}. "
            "The diagnostic agent must not approve, reject, modify, or "
            "execute robot actions."
        )
