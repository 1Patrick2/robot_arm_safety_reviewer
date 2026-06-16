import json
from pathlib import Path

import pytest

from diagnostic_runtime.agent.runner import run_diagnostic_agent

SAMPLE_CONTEXT = {
    "episode_id": "ep_deepseek_smoke",
    "total_steps": 2,
    "approved_steps": 1,
    "blocked_steps": 1,
    "rejected_steps": 1,
    "critical_steps": [
        {
            "step_index": 1,
            "decision": "reject",
            "min_clearance": -0.05,
            "closest_robot_link": "link_3",
            "closest_obstacle": "sphere_01",
        },
    ],
    "limitations": ["Diagnostic only, no execution."],
}

pytestmark = pytest.mark.skipif(
    not __import__("os").environ.get("DEEPSEEK_API_KEY"),
    reason="DEEPSEEK_API_KEY not set",
)


class TestDeepSeekDiagnosticSmoke:
    def test_deepseek_returns_report(self, tmp_path):
        context_path = tmp_path / "context.json"
        context_path.write_text(json.dumps(SAMPLE_CONTEXT), encoding="utf-8")
        output_dir = tmp_path / "deepseek_output"

        result = run_diagnostic_agent(
            context_path=context_path,
            output_dir=output_dir,
            provider="deepseek",
        )

        assert result["provider"] == "deepseek"
        report_path = Path(result["report_path"])
        assert report_path.exists()
        report_text = report_path.read_text(encoding="utf-8")
        assert "ep_deepseek_smoke" in report_text
