import pytest

from diagnostic_runtime.guardrails.safety_check import check_agent_report, check_agent_report_or_raise


class TestCheckAgentReport:
    def test_clean_report_returns_empty(self):
        report = "This is a diagnostic report. Nothing unusual."
        violations = check_agent_report(report)
        assert violations == []

    def test_detects_approve_action(self):
        report = "I approve this action because it looks safe."
        violations = check_agent_report(report)
        assert "approve this action" in violations

    def test_detects_safe_to_execute(self):
        report = "Based on the data, this action is safe to execute."
        violations = check_agent_report(report)
        assert "safe to execute" in violations

    def test_case_insensitive(self):
        report = "I APPROVE THIS ACTION immediately."
        violations = check_agent_report(report)
        assert "approve this action" in violations

    def test_raises_on_violation(self):
        report = "Modify the target joints to [0.1, 0.2, 0.0, 0.0, 0.0, 0.0]"
        with pytest.raises(ValueError, match="forbidden pattern"):
            check_agent_report_or_raise(report)

    def test_multiple_patterns(self):
        report = "I approve this action and it is safe to execute."
        violations = check_agent_report(report)
        assert len(violations) >= 2
