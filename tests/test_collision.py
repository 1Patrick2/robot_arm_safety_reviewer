from robot_arm.collision import segment_sphere_collision
from robot_arm.models import SphereObstacle


def test_segment_sphere_collision_detects_intersection():
    sphere = SphereObstacle("sphere_01", (0.5, 0.0, 0.0), 0.2)

    assert segment_sphere_collision((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), sphere)


def test_segment_sphere_collision_rejects_clear_segment():
    sphere = SphereObstacle("sphere_01", (0.5, 0.5, 0.0), 0.1)

    assert not segment_sphere_collision((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), sphere)
