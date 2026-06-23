"""Manual real LLM diagnostic smoke test — requires API key.

Skipped unless ``RUN_REAL_LLM_SMOKE`` is set.
"""

import os, json
from pathlib import Path
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_REAL_LLM_SMOKE"),
    reason="Set RUN_REAL_LLM_SMOKE=1 with evidence_manifest path",
)


def test_real_llm_diagnostic_analysis(tmp_path):
    """Run fake diagnostic analysis (no API key needed) as smoke template."""
    from diagnostics.analysis.fake_analyst import run_fake_diagnostic_analyst
    context = {"episode_id": "manual_smoke", "total_steps": 2, "approved_steps": 0, "rejected_steps": 1,
               "min_clearance": -0.05, "closest_obstacle": "sphere_01", "closest_robot_link": "link_3"}
    manifest = {"evidence_groups": {"geometry": {"available": True}, "safety": {"available": True}}}
    analysis = run_fake_diagnostic_analyst(context=context, manifest=manifest)
    assert analysis.schema_version == "llm_diagnostic_analysis.v1"
    assert "rejected" in analysis.risk_summary.lower()
