import json
from pathlib import Path
from unittest.mock import patch

import pytest

from diagnostic_agent.runner import run_diagnostic_agent

SAMPLE_CONTEXT = {
    "episode_id": "ep_001",
    "total_steps": 2,
    "approved_steps": 1,
    "blocked_steps": 1,
    "rejected_steps": 1,
    "critical_steps": [
        {"step_index": 1, "decision": "reject", "min_clearance": -0.05},
    ],
    "limitations": ["Diagnostic only, no execution."],
}


class TestFakeDiagnosticAgent:
    def test_fake_adapter_returns_report(self, tmp_path):
        context_path = tmp_path / "context.json"
        context_path.write_text(json.dumps(SAMPLE_CONTEXT), encoding="utf-8")
        output_dir = tmp_path / "output"

        result = run_diagnostic_agent(
            context_path=context_path,
            output_dir=output_dir,
            provider="fake",
        )

        assert result["provider"] == "fake"
        assert "report_path" in result
        report_path = Path(result["report_path"])
        assert report_path.exists()
        report_text = report_path.read_text(encoding="utf-8")
        assert "ep_001" in report_text

    def test_fake_report_mentions_reject_step(self, tmp_path):
        context_path = tmp_path / "context.json"
        context_path.write_text(json.dumps(SAMPLE_CONTEXT), encoding="utf-8")
        output_dir = tmp_path / "output2"

        result = run_diagnostic_agent(
            context_path=context_path,
            output_dir=output_dir,
            provider="fake",
        )
        report_text = Path(result["report_path"]).read_text(encoding="utf-8")
        assert "reject" in report_text

    def test_fake_report_passes_safety_check(self, tmp_path):
        """Fake agent output should not trigger safety violations."""
        context_path = tmp_path / "context.json"
        context_path.write_text(json.dumps(SAMPLE_CONTEXT), encoding="utf-8")
        result = run_diagnostic_agent(
            context_path=context_path,
            output_dir=tmp_path / "output3",
            provider="fake",
        )
        assert result.get("safety_violations") == []


class TestDeepSeekProviderBranch:
    """Test that the deepseek provider branch correctly calls the adapter."""

    def test_calls_deepseek_adapter_and_writes_report(self, tmp_path):
        """Mock run_deepseek_agent to verify the runner wires it correctly."""
        context_path = tmp_path / "context.json"
        context_path.write_text(json.dumps(SAMPLE_CONTEXT), encoding="utf-8")
        output_dir = tmp_path / "ds_output"

        with patch("diagnostic_agent.runner.run_deepseek_agent") as mock_fn:
            mock_fn.return_value = "# Mock DeepSeek Report\n\nEvidence check."
            result = run_diagnostic_agent(
                context_path=context_path,
                output_dir=output_dir,
                provider="deepseek",
            )

        assert result["provider"] == "deepseek"
        assert "report_path" in result
        mock_fn.assert_called_once()
        # Verify the full context dict was passed to the adapter
        called_context = mock_fn.call_args[0][0]
        assert called_context["episode_id"] == "ep_001"
        assert called_context["total_steps"] == 2

        report_path = Path(result["report_path"])
        assert report_path.exists()
        report_text = report_path.read_text(encoding="utf-8")
        assert "Mock DeepSeek Report" in report_text
        # Safety violations should be listed (empty = clean)
        assert result.get("safety_violations") == []
