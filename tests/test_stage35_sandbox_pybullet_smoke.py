import importlib
from pathlib import Path

import pytest

from application.sandbox_service import SandboxRunRequest, run_sandbox

SAMPLES = Path(__file__).resolve().parents[1] / "samples" / "policy_sequences"
BENCH = Path(__file__).resolve().parents[1] / "bench" / "sim_robot_arm"

_pybullet = importlib.util.find_spec("pybullet")
pytestmark = pytest.mark.skipif(
    _pybullet is None,
    reason="pybullet is not available in this environment",
)


class TestSandboxPyBulletSmoke:
    def test_pybullet_sandbox_produces_artifacts(self, tmp_path):
        result = run_sandbox(
            SandboxRunRequest(
                sequence_path=SAMPLES / "simple_safe_sequence.json",
                scene_path=BENCH / "simple_joint_move_001" / "scene.json",
                backend_name="pybullet",
                output_root=tmp_path,
            )
        )

        assert result.sequence_runtime_result.total_steps == 2
        assert result.episode_summary_path.exists()
        assert result.clearance_curve_path.exists()
        assert result.trajectory_overview_path.exists()
