# Mock RealMan 6-DOF URDF

This URDF is a simplified mock RealMan-style 6-DOF arm for validating the PyBullet safety backend.
It is not a calibrated RealMan robot model.

The model intentionally uses simple box collision geometry, approximate link lengths, and default Stage 1 joint limits. It is meant for kinematic safety replay and collision-query development, not dynamics, torque control, or hardware calibration.
