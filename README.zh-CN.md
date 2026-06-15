# Robot Action Safety Sandbox 中文说明

[English README](README.md)

这是一个面向机械臂动作安全审查的轻量级运行沙盒。项目最初名为 `RobotArmSafetyReviewer`，现在已经从单步安全审查器扩展为：接收策略动作、执行确定性安全审查、只放行安全动作、记录 episode，并生成运行证据的 Robot Action Safety Sandbox。

它不是路径规划器，不替代 MoveIt / Isaac / LeRobot，不训练 VLA，也不让 Agent 直接控制机器人。

## 项目能做什么

- 审查 `current_joints -> target_joints` 关节空间指令。
- 将 `PolicyActionSequence` 转为逐步 `RobotAction`。
- 支持 `joint_target` 和 `delta_joint` 两类策略动作。
- 检查关节限位、插值轨迹碰撞、最小间隙和大幅关节运动风险。
- 输出 `approve`、`manual_review` 或 `reject`。
- 只有 `approve` 才会调用 `RobotDeviceAdapter.send_action()`。
- `manual_review` 和 `reject` 会被阻断并记录原因。
- 将运行过程记录为 `metadata.json` 和 `steps.jsonl`。
- 通过 dataset adapter 读取本地样例数据。
- 生成可展示的 sandbox 证据：`episode_summary.md`、`clearance_curve.png`、`trajectory_overview.png`。

## 当前阶段

当前状态：**Stage 3.5 Visual Runtime Sandbox 已完成**。

已完成：

- Stage 1：确定性 safety gate。
- Stage 1.5：benchmark、scorer、replay、report 闭环。
- Stage 2：backend 抽象、PyBullet 诊断、mock-vs-PyBullet 对比、URDF 校准诊断。
- Stage 3.1：application service、统一 CLI、共享输出格式。
- Stage 3.2：`PolicyAction` 和 `PolicyActionSequence`。
- Stage 3.3：多步 sequence runtime。
- Stage 3.4：Dataset Adapter MVP，支持 `mini_sequence` 和本地 `lerobot_style` 样例。
- Stage 3.5：从 episode 生成 Markdown 和 PNG 可视化证据。

下一步建议：

- Stage 3.6 Runtime Metrics DB：用 SQLite 存储 run、step、decision、clearance、closest link/obstacle 和 artifact path。

暂不推进：

- DeepSeek 诊断 Agent。
- RealMan SDK 或真实硬件执行。
- ROS2 / MoveIt。
- VLA 或自主机器人控制 Agent。
- 大规模远程数据集接入。

## 安全边界

安全判定必须保持确定性。LLM 或未来 Agent 不能决定 `approve`、`manual_review` 或 `reject`。

只有 `approve` 会进入机器人设备执行层。

`manual_review` 和 `reject` 只会记录并阻断。

当前 mock 6-DOF 模型和 PyBullet backend 都是诊断仿真工具，不是真实 RealMan 数字孪生，也不是硬件安全认证。

## 快速开始

推荐 Windows 环境：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe --version
D:\miniforge3\envs\robotarm-pybullet\python.exe -c "import pybullet as p; print('pybullet ok')"
```

运行目标测试时使用项目本地临时目录：

```powershell
New-Item -ItemType Directory -Force .pytest_tmp | Out-Null
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage33_sequence_runtime.py -q --basetemp .pytest_tmp\current
```

### 审查单条指令

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main review ^
  --scene bench\sim_robot_arm\obstacle_collision_001\scene.json ^
  --command bench\sim_robot_arm\obstacle_collision_001\command.json ^
  --backend mock ^
  --log-dir logs ^
  --json
```

### 运行单步 runtime task

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main runtime run ^
  --task bench\sim_robot_arm\simple_joint_move_001 ^
  --backend mock ^
  --episode-root output_reports\runtime_demo ^
  --json
```

### 运行策略动作序列

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main sequence run ^
  --sequence samples\policy_sequences\simple_safe_sequence.json ^
  --scene bench\sim_robot_arm\simple_joint_move_001\scene.json ^
  --backend mock ^
  --episode-root output_reports\sequence_runtime ^
  --json
```

使用 `--continue-on-block` 可以在遇到 `manual_review` 或 `reject` 后继续记录后续步骤。

### 列出 dataset sequences

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main dataset list ^
  --adapter mini_sequence ^
  --source samples\policy_sequences ^
  --json
```

本地 LeRobot-style 样例：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main dataset list ^
  --adapter lerobot_style ^
  --source samples\lerobot_style ^
  --json
```

### 导出 dataset sequence

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main dataset export-sequence ^
  --adapter mini_sequence ^
  --source samples\policy_sequences ^
  --sequence-id simple_safe_sequence_001 ^
  --output output_reports\exported_sequence.json ^
  --json
```

### 运行 visual sandbox

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main sandbox run ^
  --sequence samples\policy_sequences\simple_safe_sequence.json ^
  --scene bench\sim_robot_arm\simple_joint_move_001\scene.json ^
  --backend mock ^
  --output-root output_reports\sandbox ^
  --json
```

生成的 episode 证据包括：

```text
metadata.json
steps.jsonl
episode_summary.md
clearance_curve.png
trajectory_overview.png
```

## 架构概览

```text
PolicyActionSequence / dataset sample
  -> application service
  -> SafetyRuntime.step()
  -> deterministic safety review
  -> approve: RobotDeviceAdapter.send_action()
  -> manual_review / reject: block execution
  -> EpisodeRecorder
  -> reports / visual artifacts
```

主要模块：

```text
robot_safety/                 确定性安全模型、轨迹、碰撞、评估、评分
sim/                          backend 抽象、mock backend、PyBullet backend、诊断
robot_runtime/                runtime action、observation、device、sequence、episode recorder/loader
dataset_adapters/             mini_sequence 和本地 LeRobot-style adapters
application/                  runtime、sequence、dataset、review、sandbox service
cli/                          统一命令行入口
reports/                      safety report 和 runtime visual artifacts
gateway/                      legacy safety gate 和可回放执行日志
robots/                       底层 mock RealMan-compatible adapter
```

## Benchmark 任务

Stage 1 包含 8 个仿真任务：

```text
simple_joint_move_001          approve
joint_limit_violation_001      reject
obstacle_collision_001         reject
mid_trajectory_collision_001   reject, nonzero worst-step collision
near_miss_clearance_001        manual_review
long_motion_delta_risk_001     manual_review
multi_obstacle_clearance_001   approve
invalid_command_001            reject
```

`obstacle_collision_001` 验证初始姿态已碰撞时的 fail-safe rejection。`mid_trajectory_collision_001` 验证插值轨迹中途碰撞。

## 项目文档

- [当前状态](docs/project_current_status.md)
- [项目架构](docs/project_architecture.md)
- [核心函数地图](docs/core_function_map.md)
- [Stage 2 backend diagnostics](docs/stage2_backend_diagnostics.zh-CN.md)
- [Stage 3 runtime MVP design](docs/stage3_runtime_mvp_design.md)
- [LeRobot interface study](docs/lerobot_interface_study.md)
- [Windows PyBullet setup](docs/windows_pybullet_setup.md)
- [面试说明](docs/interview_notes.md)

## Roadmap

近期：

- Stage 3.6 Runtime Metrics DB。
- 对 dataset-backed sequence runs 做批量指标汇总。
- metrics 和 failure traces 可查询后，再做 diagnostic-only Agent tools。

后续：

- PyBulletRobotDevice 或更丰富的 simulation device boundary。
- RealMan SDK 调研、dry-run、shadow mode，再到有限安全执行。
- workspace、speed、acceleration、self-collision 规则。
- 更大的 dataset adapters，但必须 optional 且 test-skippable。
