from robot.backends.backend_factory import create_backend
from robot.backends.base import BackendReviewResult
from robot.backends.mock_backend import MockGeometryBackend
from robot.backends.pybullet_backend import DEFAULT_CLOSEST_POINT_DISTANCE, PyBulletBackend
from robot.backends.backend_factory import create_backend as legacy_create_backend
from robot.backends.base import BackendReviewResult as LegacyBackendReviewResult
from robot.backends.mock_backend import MockGeometryBackend as LegacyMockGeometryBackend
from robot.backends.pybullet_backend import DEFAULT_CLOSEST_POINT_DISTANCE as LEGACY_DEFAULT_CLOSEST_POINT_DISTANCE
from robot.backends.pybullet_backend import PyBulletBackend as LegacyPyBulletBackend


def test_robot_backends_new_package_path_matches_legacy_path():
    assert create_backend is legacy_create_backend
    assert BackendReviewResult is LegacyBackendReviewResult
    assert MockGeometryBackend is LegacyMockGeometryBackend
    assert PyBulletBackend is LegacyPyBulletBackend
    assert DEFAULT_CLOSEST_POINT_DISTANCE == LEGACY_DEFAULT_CLOSEST_POINT_DISTANCE
