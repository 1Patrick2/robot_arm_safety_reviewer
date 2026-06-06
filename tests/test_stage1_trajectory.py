import pytest

from robot_safety.trajectory import compute_max_joint_delta, interpolate_joint_trajectory


def test_interpolate_joint_trajectory_includes_endpoints():
    trajectory = interpolate_joint_trajectory([0.0, 0.0], [1.0, 2.0], 3)

    assert trajectory == [(0.0, 0.0), (0.5, 1.0), (1.0, 2.0)]


def test_interpolate_joint_trajectory_rejects_invalid_steps():
    with pytest.raises(ValueError, match="steps"):
        interpolate_joint_trajectory([0.0], [1.0], 1)


def test_interpolate_joint_trajectory_rejects_dimension_mismatch():
    with pytest.raises(ValueError, match="same dimension"):
        interpolate_joint_trajectory([0.0, 1.0], [1.0], 3)


def test_compute_max_joint_delta():
    assert compute_max_joint_delta([0.0, -0.5, 0.2], [0.4, 0.1, -0.1]) == pytest.approx(0.6)

