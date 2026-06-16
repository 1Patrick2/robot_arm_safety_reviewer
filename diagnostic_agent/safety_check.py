# Compatibility wrapper — delegates to diagnostic_runtime.guardrails.
from diagnostic_runtime.guardrails.safety_check import (  # noqa: F401
    FORBIDDEN_PATTERNS,
    check_agent_report,
    check_agent_report_or_raise,
)
