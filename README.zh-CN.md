# RobotArmSafetyReviewer 中文说明

[English README](README.md)

项目文档：

- [项目架构](docs/project_architecture.md)
- [核心函数地图](docs/core_function_map.md)
- [面试笔记](docs/interview_notes.md)
- [LeRobot 接口调研](docs/lerobot_interface_study.md)
- [Stage 3 Runtime MVP 设计](docs/stage3_runtime_mvp_design.md)
- [当前状态](docs/project_current_status.md)
- [Stage 2 后端诊断](docs/stage2_backend_diagnostics.zh-CN.md)

Stage 3 runtime MVP demo：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.run_runtime_demo ^
  --task bench\sim_robot_arm\simple_joint_move_001 ^
  --backend mock ^
  --episode-dir output_reports\runtime_demo ^
  --json
```

面向 6 自由度机械臂关节空间指令的 simulation-first 安全审查中间件。

RobotArmSafetyReviewer 会在候选机械臂指令执行前进行安全审查，检查关节限位、插值轨迹碰撞、最小间隙和大幅关节运动风险。它不会自动规划绕障路径，而是输出 `approve`、`manual_review` 或 `reject`，并生成可回放日志和 Markdown 安全报告。

## 项目能做什么

- 审查 `current_joints -> target_joints` 关节空间指令。
- 对 6 自由度关节轨迹做确定性线性插值。
- 使用简化 mock 6-DOF 正运动学链路作为基线。
- 检查关节限位、连杆-球体碰撞、最小间隙和关节运动幅度。
- 输出结构化 `SafetyResult` JSON。
- 写入可回放 execution log。
- 用结构化 `expected.json` 对 benchmark 任务打分。
- 从日志重算 safety result，验证审查结果可复现。
- 生成 Markdown 安全报告和可选 3D 可视化图。
- 只有在 `approve` 时才通过 `MockRealMan6DoFAdapter` 模拟执行。

## 当前阶段

Stage 1 MVP 聚焦确定性 safety gate。Stage 1.5 在 safety gate 外补齐 benchmark、scorer 和 replay 闭环。

Stage 2 增加了 backend-agnostic 安全审查和 PyBullet 诊断能力：

- `SimulationBackend` 抽象
- `MockGeometryBackend` 确定性基线后端
- 基于 URDF 轨迹回放的 `PyBulletBackend`
- 基于 PyBullet closest-point 的碰撞几何查询
- 日志和报告中的 backend metadata
- backend smoke benchmark
- mock-vs-PyBullet 对比
- PyBullet 几何诊断
- URDF-vs-mock 标定诊断

当前 Stage 1.5 基线状态：

```text
Benchmark: 8 / 8 passed
Decision accuracy: 100%
Risk accuracy: 100%
Violation match: 100%
Gateway execution match: 100%
Replay consistency: passed
```

当前公司电脑上的 Stage 2 环境已验证：

```text
Python: D:\miniforge3\envs\robotarm-pybullet\python.exe
PyBullet: available
pytest: 113 passed
PyBullet smoke benchmark: passed
```

## 重要建模边界

当前正运动学不是标定后的真实 RealMan 机械臂模型。它是一个确定性的 mock 6-DOF 串联链路，用来验证 safety review pipeline。后续可以用 PyBullet URDF backend、RealMan SDK 状态快照、ROS2 或 MoveIt-style planning scene 替换底层模型，同时保留 safety result schema、日志、报告和 gateway 结构。

Stage 2 已包含 PyBullet URDF backend，但它仍然是仿真诊断后端，不是经过认证的真实机械臂数字孪生。PyBullet backend 使用 URDF collision geometry 和 closest-point query；mock backend 使用简化 FK segment。两者结果有差异是正常的，详见 `docs/stage2_backend_diagnostics.md`。

Stage 1 使用线性 joint-space interpolation，不是时间参数化轨迹规划。`speed` 会进入日志和报告，但速度、加速度等动态安全约束属于后续工作。

Stage 1 不实现 self-collision，只会显式记录 self-collision 是否被检查。

`MockRealMan6DoFAdapter` 不是物理仿真器，也不是真实 RealMan 数字孪生。它只是内存中的 `RobotAdapter`，用于验证 safety gate、execution boundary、adapter result logging 和 CLI 行为。

项目不会执行被拒绝或需要人工复核的指令。只有 `approve` 指令会进入 RobotAdapter 执行层。

## 环境配置

Windows 下推荐使用独立 conda/miniforge 环境，不建议把 PyBullet 硬装进项目原来的 `.venv Python 3.11.9`。

当前公司电脑已配置：

```text
Miniforge: D:\miniforge3
Conda env: D:\miniforge3\envs\robotarm-pybullet
Python: 3.10.20
```

推荐直接用环境里的 Python 跑命令：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe --version
D:\miniforge3\envs\robotarm-pybullet\python.exe -c "import pybullet as p; print('pybullet ok')"
```

如果要激活环境：

```powershell
D:\miniforge3\Scripts\conda.exe activate robotarm-pybullet
```

如果 PowerShell 提示没有初始化 conda，可以执行：

```powershell
D:\miniforge3\Scripts\conda.exe init powershell
```

然后重新打开 PowerShell，再执行：

```powershell
conda activate robotarm-pybullet
```

确认没有串到 `.venv`：

```powershell
where.exe python
python -c "import sys; print(sys.executable)"
```

输出应该指向：

```text
D:\miniforge3\envs\robotarm-pybullet\python.exe
```

如果 pytest 在 Windows 临时目录上出问题，可以使用项目本地临时目录：

```powershell
New-Item -ItemType Directory -Force .pytest_tmp | Out-Null
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp\current
```

## 快速开始

运行全量测试：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp\current
```

只审查指令，不模拟执行：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.review_command ^
  --scene bench\sim_robot_arm\obstacle_collision_001\scene.json ^
  --command bench\sim_robot_arm\obstacle_collision_001\command.json ^
  --log-dir logs
```

示例输出：

```text
Decision: reject
Risk Level: high
Min Clearance: -0.105
Closest Link: link_3
Closest Obstacle: sphere_01
Worst Step: 0
Log Path: logs\exec_YYYYMMDD_HHMMSS_xxxxxxxx.json
```

这个例子是初始姿态已经碰撞：`link_3` 和 `sphere_01` 在 `worst_step = 0` 发生重叠，`min_clearance = -0.105 m`。它验证的是环境碰撞检测和 fail-safe rejection，不是中途碰撞语义。

只在安全时模拟执行：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.execute_if_safe ^
  --scene bench\sim_robot_arm\simple_joint_move_001\scene.json ^
  --command bench\sim_robot_arm\simple_joint_move_001\command.json ^
  --log-dir logs
```

从日志生成 Markdown 报告：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.generate_report ^
  --log logs\exec_YYYYMMDD_HHMMSS_xxxxxxxx.json ^
  --output-dir output_reports ^
  --skip-plot
```

去掉 `--skip-plot` 后，如果 Matplotlib 可用，会额外生成 PNG 3D 可视化图。

运行 Stage 1 scored benchmark：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.run_benchmark ^
  --backend mock ^
  --bench bench\sim_robot_arm ^
  --log-dir logs\benchmark ^
  --output-json output_reports\stage1_benchmark_summary.json ^
  --output-md output_reports\stage1_benchmark_summary.md
```

回放一个 execution log 并比较重算结果：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.replay_log ^
  --log logs\exec_YYYYMMDD_HHMMSS_xxxxxxxx.json
```

运行 PyBullet backend smoke benchmark：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.run_benchmark ^
  --backend pybullet ^
  --mode smoke ^
  --bench bench\sim_robot_arm
```

对比 mock 和 PyBullet 后端：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.compare_backends ^
  --bench bench\sim_robot_arm ^
  --backends mock pybullet ^
  --output-json output_reports\backend_comparison.json ^
  --output-md output_reports\backend_comparison.md
```

生成 PyBullet 几何诊断：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.diagnose_backend_geometry ^
  --task bench\sim_robot_arm\mid_trajectory_collision_001 ^
  --output-json output_reports\mid_trajectory_geometry_diagnostics.json
```

生成 URDF-vs-mock 标定诊断：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.calibrate_urdf_geometry ^
  --task bench\sim_robot_arm\mid_trajectory_collision_001 ^
  --output-json output_reports\mid_trajectory_urdf_calibration.json
```

## 架构

```text
scene.json + command.json
  -> robot_safety.evaluate_joint_command
  -> SafetyResult
  -> gateway safety log
  -> Markdown report / optional 3D plot
  -> MockRealManAdapter simulated execution when approved
```

execution log 包含 schema version、input paths、review summary、trajectory summary、environment metadata、完整 scene/command payload、safety result 和 execution/adapter result。

主要模块：

```text
robot_safety/models.py        scene、command、result 结构化模型
robot_safety/trajectory.py    关节空间插值和 delta 指标
robot_safety/kinematics.py    简化确定性 6-DOF FK
robot_safety/collision.py     link-sphere clearance 和碰撞检查
robot_safety/safety_rules.py  rule-based decision logic
robot_safety/evaluator.py     safety gate orchestration
robot_safety/scorer.py        expected-contract scoring
robot_safety/benchmark.py     benchmark discovery、execution、summary
gateway/                      review 和可回放 execution log
reports/                      Markdown 报告和可选 3D 可视化
robots/                       RobotAdapter 和 MockRealMan6DoFAdapter
sim/                          backend 抽象、mock backend、PyBullet backend、diagnostics
cli/                          命令行入口
```

## Benchmark 任务

Stage 1 包含 8 个仿真任务：

```text
simple_joint_move_001          approve
joint_limit_violation_001      reject
obstacle_collision_001         reject
mid_trajectory_collision_001   reject, with nonzero worst-step collision
near_miss_clearance_001        manual_review
long_motion_delta_risk_001     manual_review
multi_obstacle_clearance_001   approve, with closest object/link reporting
invalid_command_001            reject, with structured invalid-command log
```

每个任务包含：

```text
scene.json
command.json
expected.json
```

`expected.json` 使用结构化契约，包括 `expected_safety`、`expected_gateway`、`required_output_fields` 和 `clearance_assertion`。这样 benchmark 对小幅 FK 数值漂移有容忍度，同时仍然检查 decision、risk、violation、critical obstacle attribution 和 gateway execution behavior。

`obstacle_collision_001` 验证初始姿态已经碰撞时的 fail-safe rejection。`mid_trajectory_collision_001` 验证插值轨迹在非零 step 中途撞到障碍物的情况。

## Roadmap

近期：

- backend-specific benchmark expectations
- PyBullet diagnostics visual replay
- optional expected JSON schema file

后续：

- box/table obstacle support
- workspace 和 speed safety rules
- GUI replay / screenshot
- RealMan SDK adapter skeleton
- Agent-ready command review tools
- learning-based risk triage，但只能作为 advisory，不能作为最终安全裁决

## 详细计划

Stage 1 完整规划文档：

```text
docs/stage1_plan.md
```

Windows PyBullet 环境说明：

```text
docs/windows_pybullet_setup.md
```
