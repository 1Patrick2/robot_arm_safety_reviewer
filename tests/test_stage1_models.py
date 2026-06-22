import pytest

from robot.safety.models import Scene


def test_safety_config_requires_manual_review_clearance_above_min_clearance():
    with pytest.raises(ValueError, match="manual_review_clearance"):
        Scene.from_dict(
            {
                "scene_id": "bad_thresholds",
                "robot": {
                    "robot_id": "mock_realman_6dof",
                    "model_type": "mock_6dof",
                },
                "obstacles": [],
                "safety_config": {
                    "min_clearance": 0.10,
                    "manual_review_clearance": 0.05,
                },
            }
        )
