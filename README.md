# RobotArmSafetyReviewer

EN: Stage A implements a simplified 3D deterministic robot-arm safety kernel.

中文：Stage A 先实现一个简化 3D 机械臂确定性安全审查内核。

## Scope / 当前边界

Included / 当前包含：

- 4-DOF simplified 3D arm: base yaw, shoulder pitch, elbow pitch, wrist pitch
- deterministic forward kinematics
- deterministic sampling-based IK
- joint-limit checks
- segment-sphere collision checks
- strategy evaluation and ranking
- six example scenes
- pytest coverage

Not included / 当前不包含：

- LLM / AgentRuntime
- OpenAI / DeepSeek
- ROS2 / MoveIt
- hardware control
- full 6-DOF pose IK
- mesh collision

## Run / 运行

From `robot_arm_safety_reviewer/`:

```powershell
python -m pytest tests -v
python -m robot_arm.evaluator bench\robot_arm\reach_over_obstacle_001\scene.json
```

## Stage A Goal / Stage A 目标

EN: Prove that the deterministic robot-arm safety review kernel works before
adding any agent or model layer.

中文：先证明机械臂安全审查的确定性内核成立，再考虑 Agent 或模型接入。
