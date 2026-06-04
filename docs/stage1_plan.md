下面给你一份可以直接作为 **RobotArmSafetyReviewer 第一阶段总方案** 使用的版本。它已经吸收了我们前面讨论后的最终调整：**短期不依赖真实机械臂，以长期仿真为主线，用 PyBullet/Mock 6-DOF 机械臂先搭建执行前安全审查中间件**。同时保留后续接入睿尔曼机械臂、Agent、VLA/π0.7 类模型输出验证的扩展空间。

---

# RobotArmSafetyReviewer 第一阶段总方案

## 1. 第一阶段定位

第一阶段不做真实机械臂控制，也不接 LLM，不训练模型，而是先完成一个：

> **Simulation-first 6-DOF Robot Arm Safety Gate MVP**

也就是：

> 给定一个 6 轴机械臂的当前关节状态、目标关节状态、场景障碍物和安全阈值，系统在 PyBullet / Mock 仿真环境中重放关节空间轨迹，检查关节限制、轨迹碰撞、最小 clearance 和风险等级，最终输出 `approve / manual_review / reject` 的执行前安全审查结果，并生成可回放日志、Markdown 报告和 3D 可视化结果。

这和最早方案中的 Stage A 精神一致：**第一阶段先做 deterministic robot arm safety kernel，不接 LLM、不接 OpenAI/DeepSeek、不写 AgentRuntime、不接 ROS2/MoveIt**。区别是现在从原来的 4-DOF toy arm，升级为更贴近未来睿尔曼机械臂的 **6-DOF simulation-first safety middleware**。

---

# 2. 第一阶段目标

第一阶段的目标不是“让机器人完成复杂任务”，而是把一条候选机械臂动作变成可审查、可复现、可解释的安全评估流程。

核心目标：

```text
1. 建立 6-DOF 机械臂仿真模型
2. 定义 scene.json / command.json / safety_result.json 数据契约
3. 支持 joint-space trajectory 插值
4. 检查 joint limits
5. 在仿真/简化 FK 中检查 link-obstacle collision
6. 计算 min_clearance / closest_link / closest_obstacle / worst_step
7. 输出 approve / manual_review / reject
8. 生成 execution log
9. 生成 Markdown safety report
10. 生成 3D visualization
11. 提供 CLI 可直接运行
12. 添加 pytest 回归测试
```

---

# 3. 第一阶段不做什么

这一点要写进 README，避免项目跑偏。

```text
不接 LLM
不接 DeepSeek / OpenAI
不写 AgentRuntime
不写 provider adapter
不做 π0.7 / OpenVLA / SmolVLA 复现
不训练控制策略
不接真实睿尔曼机械臂
不接 ROS2
不接 MoveIt
不做完整笛卡尔 IK
不做真实抓取任务
不做复杂 VLM 感知
```

第一阶段只做：

```text
Simulation-first deterministic safety gate
```

也就是先把“一个候选动作是否安全”这件事做扎实。

---

# 4. 第一阶段核心输入输出

## 4.1 输入 1：scene.json

`scene.json` 描述仿真场景、障碍物和安全阈值。

示例：

```json
{
  "scene_id": "obstacle_collision_001",
  "robot": {
    "robot_id": "mock_realman_6dof",
    "model_type": "mock_6dof",
    "base_position": [0.0, 0.0, 0.0],
    "base_orientation": [0.0, 0.0, 0.0, 1.0],
    "joint_names": ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"],
    "link_radius": 0.025
  },
  "obstacles": [
    {
      "type": "sphere",
      "obstacle_id": "sphere_01",
      "position": [0.35, 0.10, 0.35],
      "radius": 0.08
    }
  ],
  "safety_config": {
    "min_clearance": 0.05,
    "manual_review_clearance": 0.10,
    "max_joint_delta": 1.2,
    "num_interpolation_steps": 40,
    "check_self_collision": false
  }
}
```

---

## 4.2 输入 2：command.json

`command.json` 描述待审查的机械臂动作。

第一阶段只支持 joint-space command。

```json
{
  "command_id": "cmd_unsafe_direct_001",
  "command_type": "joint_move",
  "current_joints": [0.0, -0.4, 0.8, 0.0, 0.3, 0.0],
  "target_joints": [0.6, -0.7, 1.0, -0.2, 0.5, 0.1],
  "speed": 0.2,
  "source": "mock_user"
}
```

注意：第一阶段先不做：

```json
{
  "command_type": "cartesian_goal",
  "target_pose": {}
}
```

因为笛卡尔目标会牵涉真实 IK、多解选择、末端工具坐标系等问题，暂时放到后续阶段。

---

## 4.3 输出：safety_result.json

输出结构：

```json
{
  "scene_id": "obstacle_collision_001",
  "command_id": "cmd_unsafe_direct_001",
  "decision": "reject",
  "risk_level": "high",
  "joint_limits_ok": true,
  "trajectory_collision_free": false,
  "self_collision_free": true,
  "min_clearance": -0.024,
  "closest_robot_link": "link_3",
  "closest_obstacle": "sphere_01",
  "worst_step": 22,
  "violations": [
    {
      "type": "environment_collision",
      "object": "sphere_01",
      "link": "link_3",
      "step": 22,
      "clearance": -0.024
    }
  ],
  "evidence": [
    "The interpolated trajectory collides with sphere_01 at step 22.",
    "The closest robot link is link_3.",
    "Minimum clearance is -0.024 m, below the required threshold 0.05 m."
  ]
}
```

核心决策只设置三类：

```text
approve
manual_review
reject
```

含义：

```text
approve:
无碰撞，关节合法，clearance 足够，动作可在仿真中通过。

manual_review:
没有硬性碰撞或越界，但 clearance 太小、joint delta 太大或风险偏中，需要人工确认。

reject:
发生关节越界、环境碰撞、无效命令或严重风险。
```

---

# 5. 第一阶段项目结构

建议目录如下：

```text
RobotArmSafetyReviewer/
│
├── robot_safety/
│   ├── __init__.py
│   ├── models.py
│   ├── kinematics.py
│   ├── trajectory.py
│   ├── collision.py
│   ├── safety_rules.py
│   └── evaluator.py
│
├── sim/
│   ├── __init__.py
│   ├── base.py
│   ├── mock_backend.py
│   └── pybullet_backend.py
│
├── robots/
│   ├── __init__.py
│   ├── robot_spec.py
│   ├── mock_realman_6dof.py
│   └── realman_adapter.py
│
├── gateway/
│   ├── __init__.py
│   ├── safety_gate.py
│   ├── execution_logger.py
│   └── replay.py
│
├── reports/
│   ├── __init__.py
│   ├── report_writer.py
│   └── plot_3d.py
│
├── bench/
│   └── sim_robot_arm/
│       ├── simple_joint_move_001/
│       │   ├── scene.json
│       │   ├── command_safe.json
│       │   └── expected.json
│       ├── joint_limit_violation_001/
│       ├── obstacle_collision_001/
│       ├── near_miss_clearance_001/
│       ├── long_motion_delta_risk_001/
│       └── multi_obstacle_clearance_001/
│
├── cli/
│   ├── __init__.py
│   ├── review_command.py
│   ├── replay_log.py
│   └── generate_report.py
│
├── logs/
├── output_reports/
├── tests/
│   ├── test_kinematics.py
│   ├── test_trajectory.py
│   ├── test_collision.py
│   ├── test_safety_rules.py
│   └── test_evaluator.py
│
├── docs/
│   ├── project_plan.md
│   ├── schema_design.md
│   ├── safety_rules.md
│   └── roadmap.md
│
├── README.md
├── requirements.txt
└── pyproject.toml
```

其中第一阶段最关键的是：

```text
robot_safety/
sim/
gateway/
reports/
bench/
cli/
tests/
```

---

# 6. 核心模块设计

## 6.1 robot_safety/models.py

定义所有核心数据结构。

建议使用 `dataclass` 或 `pydantic`。第一版如果想轻量，就用 `dataclass`。

核心类：

```python
JointLimit
RobotModel
RobotState
JointCommand
SphereObstacle
BoxObstacle
SafetyConfig
Scene
TrajectoryPoint
Violation
SafetyResult
```

字段建议：

```python
@dataclass
class JointLimit:
    lower: float
    upper: float

@dataclass
class RobotModel:
    robot_id: str
    joint_names: list[str]
    joint_limits: list[JointLimit]
    link_lengths: list[float]
    link_radius: float

@dataclass
class JointCommand:
    command_id: str
    current_joints: list[float]
    target_joints: list[float]
    speed: float

@dataclass
class SphereObstacle:
    obstacle_id: str
    position: list[float]
    radius: float

@dataclass
class SafetyConfig:
    min_clearance: float
    manual_review_clearance: float
    max_joint_delta: float
    num_interpolation_steps: int
    check_self_collision: bool
```

---

## 6.2 robot_safety/kinematics.py

第一阶段实现一个简化 6-DOF FK。

目标不是毫米级真实睿尔曼模型，而是构造一个可以用于 safety pipeline 验证的 mock 6-DOF arm。

函数：

```python
def forward_kinematics_6dof(robot: RobotModel, joints: list[float]) -> list[list[float]]:
    """
    Return base, joint positions, and end-effector position.
    Length should be 7 for 6-DOF arm:
    [base, joint1, joint2, joint3, joint4, joint5, ee]
    """
```

输出：

```text
base point
joint points
end-effector point
```

每两个相邻点形成一段 link segment：

```text
p0 -> p1
p1 -> p2
...
p5 -> p6
```

后续 PyBullet backend 可以替代手写 FK，但第一阶段保留手写 FK，有助于测试和 fallback。

---

## 6.3 robot_safety/trajectory.py

实现关节空间插值。

函数：

```python
def interpolate_joint_trajectory(
    current_joints: list[float],
    target_joints: list[float],
    steps: int
) -> list[list[float]]:
    ...
```

要求：

```text
包含起点和终点
steps 至少为 2
每一步维度等于关节数
线性插值 deterministic
```

再实现：

```python
def compute_max_joint_delta(current_joints, target_joints) -> float:
    ...
```

用于判断是否需要人工确认。

---

## 6.4 robot_safety/collision.py

第一阶段支持 sphere obstacle。

核心函数：

```python
def distance_segment_to_point(p1, p2, point) -> float:
    ...
```

```python
def segment_sphere_clearance(p1, p2, sphere, link_radius: float) -> float:
    """
    clearance = distance(segment, sphere.center) - sphere.radius - link_radius
    """
```

```python
def check_state_collision(points, obstacles, link_radius) -> StateCollisionResult:
    ...
```

```python
def check_trajectory_collision(trajectory_points, robot, obstacles) -> TrajectoryCollisionResult:
    ...
```

需要记录：

```text
min_clearance
closest_link
closest_obstacle
worst_step
collision_free
violations
```

---

## 6.5 robot_safety/safety_rules.py

负责决策逻辑。

核心检查：

```python
def check_joint_limits(joints, joint_limits) -> tuple[bool, list[Violation]]:
    ...
```

```python
def check_trajectory_joint_limits(trajectory, joint_limits) -> tuple[bool, list[Violation]]:
    ...
```

```python
def classify_risk_level(
    joint_limits_ok: bool,
    collision_free: bool,
    min_clearance: float,
    max_joint_delta: float,
    config: SafetyConfig
) -> str:
    ...
```

```python
def make_decision(...) -> str:
    ...
```

建议规则：

```text
如果 joint limit violation:
    decision = reject
    risk_level = high

如果 collision:
    decision = reject
    risk_level = high

如果 min_clearance < min_clearance:
    decision = reject
    risk_level = high

如果 min_clearance < manual_review_clearance:
    decision = manual_review
    risk_level = medium

如果 max_joint_delta > max_joint_delta:
    decision = manual_review
    risk_level = medium

否则:
    decision = approve
    risk_level = low
```

---

## 6.6 robot_safety/evaluator.py

这是第一阶段核心入口。

函数：

```python
def evaluate_joint_command(scene: Scene, command: JointCommand) -> SafetyResult:
    ...
```

内部流程：

```text
1. 校验 joints 维度
2. 生成 joint trajectory
3. 检查每个 trajectory state 的 joint limits
4. 对每个 state 做 FK
5. 对每个 link 和 obstacle 做 clearance/collision 检查
6. 统计 min_clearance / closest_link / closest_obstacle / worst_step
7. 生成 violations
8. 生成 decision / risk_level
9. 生成 evidence
10. 返回 SafetyResult
```

---

## 6.7 sim/mock_backend.py

第一阶段可以先有 mock backend。

它调用手写 FK 和 collision：

```python
class MockSimulationBackend:
    def load_scene(self, scene: Scene) -> None:
        ...

    def replay_trajectory(self, trajectory: list[list[float]]) -> SimReplayResult:
        ...
```

Mock backend 的作用：

```text
不用安装 PyBullet 也能跑测试
给 PyBullet backend 提供统一接口参照
```

---

## 6.8 sim/pybullet_backend.py

如果第一阶段时间允许，加入 PyBullet backend。

功能：

```text
加载 URDF 或 mock 6DOF URDF
加载 sphere / box obstacles
设置 joint states
重放 trajectory
检查 collision
保存 screenshot 或 debug state
```

第一阶段可以做成 optional：

```text
如果安装了 pybullet，则启用
如果没安装，则 fallback 到 mock_backend
```

这能降低环境风险。

---

## 6.9 gateway/safety_gate.py

实现执行前安全网关。

第一阶段不真的执行硬件，只做 simulated approval。

函数：

```python
def review_only(scene_path: str, command_path: str) -> SafetyResult:
    ...
```

```python
def execute_if_safe(scene_path: str, command_path: str, robot_adapter: str = "mock") -> ExecutionLog:
    ...
```

逻辑：

```text
如果 approve:
    simulated_execution.executed = true

如果 manual_review:
    simulated_execution.executed = false
    reason = manual_review_required

如果 reject:
    simulated_execution.executed = false
    reason = rejected_by_safety_gate
```

---

## 6.10 gateway/execution_logger.py

每次审查写入 log。

日志结构：

```json
{
  "log_id": "exec_20260604_001",
  "timestamp": "2026-06-04T14:00:00+09:00",
  "scene_id": "obstacle_collision_001",
  "command_id": "cmd_unsafe_direct_001",
  "robot": "mock_realman_6dof",
  "scene": {},
  "command": {},
  "safety_result": {},
  "execution": {
    "executed": false,
    "reason": "rejected_by_safety_gate"
  }
}
```

---

## 6.11 reports/report_writer.py

根据 log 或 safety_result 生成 Markdown。

报告结构：

```text
# Robot Arm Safety Review Report

## Task Summary
- Scene ID
- Command ID
- Robot
- Decision
- Risk Level

## Robot Command
- Current joints
- Target joints
- Max joint delta

## Safety Checks
| Check | Result |
|---|---|
| Joint limits | PASS / FAIL |
| Environment collision | PASS / FAIL |
| Minimum clearance | value |
| Risk level | low / medium / high |

## Critical Evidence
- ...

## Violations
- ...

## Execution Decision
- approve / manual_review / reject

## Replay
- log path
- visualization path
```

---

## 6.12 reports/plot_3d.py

生成 matplotlib 3D 图。

第一阶段画：

```text
current posture
target posture
worst-step posture
sphere obstacles
closest link-obstacle pair
target trajectory keyframes
```

图里不需要特别花哨，但要清晰展示：

```text
机械臂
障碍物
最危险位置
是否碰撞
```

---

# 7. CLI 设计

## 7.1 审查命令

```bash
python -m cli.review_command \
  --scene bench/sim_robot_arm/obstacle_collision_001/scene.json \
  --command bench/sim_robot_arm/obstacle_collision_001/command_unsafe.json
```

输出：

```text
Decision: reject
Risk Level: high
Min Clearance: -0.024
Closest Link: link_3
Closest Obstacle: sphere_01
Worst Step: 22
```

同时保存：

```text
logs/*.json
```

---

## 7.2 生成报告

```bash
python -m cli.generate_report \
  --log logs/exec_20260604_001.json
```

输出：

```text
output_reports/exec_20260604_001.md
output_reports/exec_20260604_001.png
```

---

## 7.3 回放日志

```bash
python -m cli.replay_log \
  --log logs/exec_20260604_001.json
```

功能：

```text
读取 log
重新生成 safety result
对比原 result
重新生成 report / visualization
```

---

# 8. 第一批 Benchmark 场景

第一阶段建议做 6 个任务。

## 8.1 simple_joint_move_001

无障碍，关节合法。

```text
expected_decision: approve
expected_risk_level: low
```

---

## 8.2 joint_limit_violation_001

目标关节超过限制。

```text
expected_decision: reject
expected_violation: joint_limit
```

---

## 8.3 obstacle_collision_001

轨迹中某个 link 与 sphere 碰撞。

```text
expected_decision: reject
expected_violation: environment_collision
expected_critical_obstacle: sphere_01
```

---

## 8.4 near_miss_clearance_001

轨迹没有碰撞，但 clearance 小于人工复核阈值。

```text
expected_decision: manual_review
expected_violation: low_clearance
```

---

## 8.5 long_motion_delta_risk_001

关节变化过大，没有碰撞，但需要人工复核。

```text
expected_decision: manual_review
expected_violation: large_joint_delta
```

---

## 8.6 multi_obstacle_clearance_001

多个障碍物，系统要识别最近障碍物和最近 link。

```text
expected_decision: approve 或 manual_review
expected_fields:
  closest_obstacle
  closest_robot_link
  min_clearance
```

---

# 9. 测试设计

## tests/test_trajectory.py

测试：

```text
插值数量正确
包含起点和终点
中间值正确
非法 steps 报错
joint 维度不一致报错
```

---

## tests/test_kinematics.py

测试：

```text
FK 输出点数量为 7
每个点是 3D 坐标
zero joints 下末端位置符合预期
改变 joint 后末端位置发生变化
```

---

## tests/test_collision.py

测试：

```text
distance_segment_to_point 正确
segment_sphere_clearance 正确
碰撞时 clearance < 0
安全时 clearance > 0
能返回 closest_link / closest_obstacle
```

---

## tests/test_safety_rules.py

测试：

```text
关节越界 reject
碰撞 reject
低 clearance manual_review
大 joint delta manual_review
安全动作 approve
```

---

## tests/test_evaluator.py

测试：

```text
simple_joint_move_001 -> approve
joint_limit_violation_001 -> reject
obstacle_collision_001 -> reject
near_miss_clearance_001 -> manual_review
long_motion_delta_risk_001 -> manual_review
multi_obstacle_clearance_001 能输出 closest 信息
```

---

# 10. 第一阶段 README 要点

README 第一版应该强调：

```text
RobotArmSafetyReviewer is a simulation-first safety middleware for 6-DOF robot arm commands.

It reviews joint-space commands before execution by checking:
- joint limits
- interpolated trajectory
- forward kinematics
- link-obstacle collision
- minimum clearance
- risk level

The current MVP does not require physical hardware.
It uses a mock 6-DOF robot model and replayable safety logs.
Future versions can integrate PyBullet URDF models, RealMan SDK, ROS2 / MoveIt-style snapshots, and Agent tool-use layers.
```

中文说明：

```text
当前版本不连接真实机械臂。
当前版本不让 LLM 控制机械臂。
当前版本先验证机械臂执行前安全审查链路。
后续真实睿尔曼机械臂接入时，只需替换 RobotAdapter / SimulationBackend。
```

---

# 11. 第一阶段和后续阶段的边界

## 第一阶段做完后的产物

```text
可运行 CLI
6 个 benchmark scenes
完整 safety_result JSON
可回放 execution log
Markdown report
3D visualization
pytest 测试
README
docs/project_plan.md
```

---

## 第二阶段再做

```text
PyBullet backend 完整化
URDF 模型
PyBullet GUI replay
更多 obstacle 类型
trajectory screenshot
benchmark scorer
```

如果第一阶段已经顺利接入 PyBullet，则第二阶段可以直接进入 Benchmark + Report 完善。

---

## 第三阶段再做

```text
Agent tool-use layer
load_scene
load_command
simulate_command
evaluate_safety
compare_candidate_commands
write_report
```

---

## 第四阶段再做

```text
RealMan adapter skeleton
RealMan joint_state example
RealMan command example
docs/realman_integration_plan.md
```

---

## 第五阶段再做

```text
LeRobot-style dataset
risk classifier
policy proposal validation
SmolVLA / ACT / Diffusion Policy optional baseline
```

这里可以吸收 π0.7 这类 steerable VLA 的思想，但项目主线不是复现 VLA，而是验证 VLA / Agent / human command 提出的候选动作是否安全。

---

# 12. 第一阶段 Codex 开发 Prompt 草案

你可以直接给 Codex 用下面这个版本。

```text
You are helping implement RobotArmSafetyReviewer Stage 1.

Project goal:
Build a simulation-first deterministic safety gate for 6-DOF robot arm joint-space commands.

Important boundaries:
- Do not implement LLM Agent.
- Do not call OpenAI, DeepSeek, or any online API.
- Do not implement AgentRuntime or provider adapters.
- Do not connect to real robot hardware.
- Do not implement ROS2 or MoveIt integration.
- Do not train any model.
- Focus on deterministic robot safety review.

Stage 1 goal:
Given a scene.json and a command.json, review whether a 6-DOF robot arm joint-space command is safe before execution.

Inputs:
1. scene.json:
- scene_id
- robot model info
- obstacles, initially sphere obstacles
- safety_config:
  - min_clearance
  - manual_review_clearance
  - max_joint_delta
  - num_interpolation_steps
  - check_self_collision

2. command.json:
- command_id
- command_type = joint_move
- current_joints
- target_joints
- speed
- source

Outputs:
SafetyResult JSON with:
- scene_id
- command_id
- decision: approve | manual_review | reject
- risk_level: low | medium | high
- joint_limits_ok
- trajectory_collision_free
- min_clearance
- closest_robot_link
- closest_obstacle
- worst_step
- violations
- evidence

Implement modules:

robot_safety/models.py:
- dataclasses for RobotModel, JointLimit, JointCommand, SphereObstacle, SafetyConfig, Scene, Violation, SafetyResult.

robot_safety/kinematics.py:
- forward_kinematics_6dof(robot, joints) -> list of 3D points.
- Use a deterministic simplified 6-DOF serial chain.
- Return base, joint positions, and end-effector position.

robot_safety/trajectory.py:
- interpolate_joint_trajectory(current_joints, target_joints, steps)
- compute_max_joint_delta(current_joints, target_joints)

robot_safety/collision.py:
- distance_segment_to_point(p1, p2, point)
- segment_sphere_clearance(p1, p2, sphere, link_radius)
- check_state_collision(points, obstacles, link_radius)
- check_trajectory_collision(trajectory, robot, obstacles)

robot_safety/safety_rules.py:
- check_joint_limits
- check_trajectory_joint_limits
- classify_risk_level
- make_decision

robot_safety/evaluator.py:
- evaluate_joint_command(scene, command) -> SafetyResult
- Generate trajectory.
- Check joint limits.
- Run FK for each trajectory step.
- Check link-sphere collision and clearance.
- Generate violations, evidence, risk_level and decision.

gateway/execution_logger.py:
- write execution log JSON.

gateway/safety_gate.py:
- review_only(scene_path, command_path)
- execute_if_safe(scene_path, command_path)
- In Stage 1 execution is simulated only.

reports/report_writer.py:
- Generate Markdown report from log or SafetyResult.

reports/plot_3d.py:
- Generate matplotlib 3D visualization showing current posture, target posture, worst-step posture, and sphere obstacles.

cli/review_command.py:
- CLI entry:
  python -m cli.review_command --scene path/to/scene.json --command path/to/command.json

cli/generate_report.py:
- Generate Markdown and PNG from a log.

cli/replay_log.py:
- Load execution log and regenerate report.

bench/sim_robot_arm:
Create 6 tasks:
1. simple_joint_move_001 -> approve
2. joint_limit_violation_001 -> reject
3. obstacle_collision_001 -> reject
4. near_miss_clearance_001 -> manual_review
5. long_motion_delta_risk_001 -> manual_review
6. multi_obstacle_clearance_001 -> approve or manual_review but must report closest link and obstacle.

tests:
Add pytest tests for:
- trajectory interpolation
- FK output shape
- collision distance and clearance
- joint limit violation
- evaluator decisions for all 6 benchmark tasks

README:
Explain:
- This is Stage 1: simulation-first robot arm safety gate.
- No LLM, no real hardware, no ROS2, no MoveIt.
- The system reviews joint-space commands using deterministic checks.
- Future extensions include PyBullet backend, RealMan adapter, Agent tool-use, and learning-based risk triage.

Keep implementation simple, deterministic, well-tested, and easy to run.
```

---

# 13. 第一阶段验收标准

第一阶段完成后，应该能做到：

```bash
pytest
```

全部通过。

并且能运行：

```bash
python -m cli.review_command \
  --scene bench/sim_robot_arm/obstacle_collision_001/scene.json \
  --command bench/sim_robot_arm/obstacle_collision_001/command_unsafe.json
```

输出类似：

```text
Decision: reject
Risk Level: high
Min Clearance: -0.024
Closest Link: link_3
Closest Obstacle: sphere_01
Worst Step: 22
```

然后运行：

```bash
python -m cli.generate_report --log logs/exec_xxx.json
```

得到：

```text
output_reports/exec_xxx.md
output_reports/exec_xxx.png
```

这就说明第一阶段闭环成立：

```text
scene + command
    ↓
trajectory review
    ↓
collision / clearance / joint limits
    ↓
decision
    ↓
log
    ↓
report + visualization
```

---

# 14. 第一阶段简历表达

第一阶段完成后，可以这样写：

> 设计并实现 RobotArmSafetyReviewer，一个仿真优先的 6 轴机械臂执行前安全审查中间件。系统基于结构化 scene/command 输入，对 joint-space 目标命令进行轨迹插值、简化 6-DOF FK、关节限制检查、连杆-球障碍物碰撞检测和 minimum clearance 评估，输出 approve / manual_review / reject 决策，并生成可回放 safety log、Markdown 审查报告和 3D 可视化结果。项目为后续接入 PyBullet URDF、睿尔曼机械臂 SDK、ROS2 / MoveIt-style snapshot 和 Agent tool-use 审查层预留了 SimulationBackend 与 RobotAdapter 抽象。

---

# 15. 最终一句话总结

第一阶段不要做 Agent，也不要做真实硬件，也不要急着训练模型。

第一阶段只做一件事：

> **把 6 轴机械臂的一条候选关节空间动作，变成可仿真、可审查、可复现、可报告的安全评估闭环。**

这就是项目二和项目一拉开差异的关键。
