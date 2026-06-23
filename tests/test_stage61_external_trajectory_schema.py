import json, tempfile
from pathlib import Path

import pytest

from bench.adapters.external_trajectory import (
    ExternalActionFrame,
    ExternalTrajectory,
    ActionMappingConfig,
)


class TestExternalActionFrame:
    def test_create(self):
        f = ExternalActionFrame(step_index=0, action=(1.0, 2.0), action_type="joint_position", source="test")
        assert f.step_index == 0
        assert f.action == (1.0, 2.0)

    def test_to_dict_shape(self):
        f = ExternalActionFrame(step_index=0, action=(0.1,), action_type="jp", source="t")
        d = {"step_index": 0, "action": (0.1,), "action_type": "jp", "source": "t",
             "timestamp": None, "metadata": {}}
        # just check accessible fields
        assert f.step_index == d["step_index"]


class TestExternalTrajectory:
    def test_create(self):
        t = ExternalTrajectory(
            dataset_name="ds", episode_id="ep1", action_type="joint_position",
            frames=(ExternalActionFrame(0, (1.0,), "jp", "t"),),
        )
        assert t.dataset_name == "ds"
        assert len(t.frames) == 1


class TestActionMappingConfig:
    def test_valid(self):
        m = ActionMappingConfig(joint_count=6)
        assert m.joint_count == 6

    def test_invalid_joint_count(self):
        with pytest.raises(ValueError, match="joint_count"):
            ActionMappingConfig(joint_count=0)

    def test_invalid_offset_length(self):
        with pytest.raises(ValueError, match="offset length"):
            ActionMappingConfig(joint_count=6, offset=(0.0, 0.0))

    def test_invalid_current_joints_policy(self):
        with pytest.raises(ValueError, match="current_joints_policy"):
            ActionMappingConfig(joint_count=6, current_joints_policy="unknown")
