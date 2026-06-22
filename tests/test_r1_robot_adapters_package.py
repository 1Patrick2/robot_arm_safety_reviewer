from robot.adapters.base import RobotAdapter, RobotExecutionResult
from robot.adapters.mock_realman_6dof import MockRealMan6DoFAdapter
from robot.adapters.base import RobotAdapter as LegacyRobotAdapter
from robot.adapters.base import RobotExecutionResult as LegacyRobotExecutionResult
from robot.adapters.mock_realman_6dof import MockRealMan6DoFAdapter as LegacyMockRealMan6DoFAdapter


def test_robot_adapters_new_package_path_matches_legacy_path():
    assert RobotAdapter is LegacyRobotAdapter
    assert RobotExecutionResult is LegacyRobotExecutionResult
    assert MockRealMan6DoFAdapter is LegacyMockRealMan6DoFAdapter
