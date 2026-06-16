# Compatibility wrapper — delegates to diagnostic_runtime.context.
from diagnostic_runtime.context.builder import build_agent_context_from_db  # noqa: F401
from diagnostic_runtime.context.builder import _normalise_step  # noqa: F401
from diagnostic_runtime.context.builder import _select_critical_steps  # noqa: F401
