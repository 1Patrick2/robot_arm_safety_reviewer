"""Manual LeRobot Hub smoke test — requires lerobot and network access.

Skipped unless ``RUN_LEROBOT_HUB_SMOKE`` is set.
"""

import os
import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_LEROBOT_HUB_SMOKE"),
    reason="Set RUN_LEROBOT_HUB_SMOKE=1 with LEROBOT_REPO_ID and LEROBOT_EPISODE_INDEX",
)


def test_load_lerobot_hub_episode():
    repo_id = os.environ.get("LEROBOT_REPO_ID", "lerobot/aloha_mobile_cabinet")
    episode_index = int(os.environ.get("LEROBOT_EPISODE_INDEX", "0"))

    from bench.adapters.optional_lerobot_hub_adapter import load_lerobot_hub_episode  # noqa: PLC0415

    traj = load_lerobot_hub_episode(repo_id, episode_index=episode_index, max_frames=10)
    assert traj.dataset_name == repo_id.replace("/", "_")
    assert len(traj.frames) > 0
    assert len(traj.frames) <= 10

    # Verify actions can be converted
    from bench.adapters.external_trajectory import (  # noqa: PLC0415
        ActionMappingConfig,
        external_trajectory_to_policy_sequence,
    )
    mapping = ActionMappingConfig(
        joint_count=len(traj.frames[0].action),
        source_action_type=traj.action_type,
    )
    seq = external_trajectory_to_policy_sequence(traj, mapping)
    assert len(seq.actions) == len(traj.frames)
