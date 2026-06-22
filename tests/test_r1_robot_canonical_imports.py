"""Verify that the canonical robot domain packages import correctly.

After R1-B6, ``robot/safety/``, ``robot/runtime/``, ``robot/backends/``,
and ``robot/adapters/`` are the only robot-domain packages.
"""


def test_robot_canonical_imports():
    import robot.safety.evaluator
    import robot.safety.models
    import robot.runtime.safety_runtime
    import robot.runtime.types
    import robot.backends.backend_factory
    import robot.backends.base
    import robot.adapters.base
    import robot.adapters.mock_realman_6dof
