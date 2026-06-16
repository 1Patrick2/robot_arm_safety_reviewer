# Compatibility wrapper — delegates to diagnostic_runtime.context.
from diagnostic_runtime.context.render import (  # noqa: F401
    render_agent_context_json,
    render_agent_context_markdown,
    write_agent_context_files,
)
