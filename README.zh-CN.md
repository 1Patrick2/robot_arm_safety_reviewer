# Robot Action Safety Sandbox 中文说明

[English README](README.md)

Robot Action Safety Sandbox 是一个机器人动作安全评测与诊断证据系统，用于对机械臂动作序列进行确定性安全评估、运行证据记录、诊断上下文构建、回归验证和可选诊断分析。

后续主线不是继续扩展泛 Agent，而是引入感知结果 schema，将人体/障碍物等感知结果转换为动态安全约束，与机械臂轨迹安全评估进行融合。

项目最初叫 `RobotArmSafetyReviewer`。它仍然是 safety reviewer，不是 motion planner。它不会静默修改轨迹，不会自动绕障，也不会让 LLM 决定机械臂动作是否安全。

本项目不是泛 Agent 项目，而是机器人动作安全评测与诊断证据系统。LLM / diagnostic analysis 只是可选诊断解释层，用于解释已有确定性证据，不参与安全裁决，不控制机器人，不修改动作。

## 当前状态

当前阶段：**v0.2 — 外部轨迹、真实LLM诊断建议、测试整合 — 已完成**。

已完成功能范围：

- **确定性安全运行时**：关节空间 safety gate、benchmark/scorer/replay、mock 和 PyBullet 后端、URDF 标定诊断。
- **策略动作流水线**：`PolicyActionSequence`、`SafetyRuntime` 多步执行、可视化沙箱证据、运行时 metrics 数据库、agent context 生成。
- **证据与诊断**：`evidence_manifest.json` 支持 evidence_groups（runtime, safety, geometry, visual, diagnostic, agent, perception, external_trajectory）、expected contract 校验、诊断回归、fake LLM analyst。
- **感知融合**：`perception_result.v1` schema、模型适配器协议、`FakePerceptionModelAdapter`、感知安全融合、推理证据桥接。
- **真实 YOLO/ONNX 感知**：`UltralyticsYoloAdapter`（lazy import）、ONNX 导出支持、手动 smoke。
- **v0.1 顶层目录整合**：16 → 9 个顶层目录。遗留包已删除。使用规范的 robot.*、perception.*、diagnostics.* 路径。
- **v0.2 外部轨迹接入**：LeRobot 风格的 episode schema、`ActionMappingConfig`、`external_trajectory_to_policy_sequence()`、轨迹证据记录、evidence manifest 集成。
- **v0.2 真实 LLM 诊断建议**：`call_llm_diagnostic_analysis()` 支持 DeepSeek、OpenAI、OpenAI-compatible 提供商。返回 `LLMFinalAnswer`。
- **v0.2 真实集成演示**：`tools/run_real_integrated_demo.py` — 端到端链路：外部轨迹 → SafetyRuntime → 可选感知 → evidence manifest → 可选 LLM → `final_answer.md`（7 个输出文件）。
- **v0.2 测试结构整合**：从 ~60 个 stage-based 测试文件缩减为 8 个 capability-level 测试 + 补充测试。遗留 `test_stage*.py` 文件已删除。测试结构按能力组织，而非按阶段组织。

## 安全边界

- 安全判定必须是确定性的：`approve`、`manual_review` 或 `reject`。
- 只有 `approve` 会进入 `RobotDeviceAdapter.send_action()`。
- `manual_review` 和 `reject` 会被阻断并记录。
- Agent context 和 diagnostic analysis 只是诊断证据，不能 approve、reject、修改或执行机器人动作。
- mock backend 和 PyBullet backend 都是诊断仿真工具，不是硬件安全认证。

暂不推进：

- RealMan SDK / 硬件执行。
- ROS2 / MoveIt。
- VLA 或自主机器人控制 Agent。
- 大规模远程数据集接入。
- 真实边缘部署、ONNX、RKNN 或摄像头接入。

## 快速开始

推荐 Windows 环境：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe --version
D:\miniforge3\envs\robotarm-pybullet\python.exe -c "import pybullet as p; print('pybullet ok')"
```

运行目标测试时使用项目本地临时目录：

```powershell
New-Item -ItemType Directory -Force .pytest_tmp | Out-Null
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage37_agent_context_builder.py -q --basetemp .pytest_tmp\current
```

## 常用命令

### 审查单条命令

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main review ^
  --scene bench\sim_robot_arm\obstacle_collision_001\scene.json ^
  --command bench\sim_robot_arm\obstacle_collision_001\command.json ^
  --backend mock ^
  --log-dir logs ^
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

### 运行带 metrics DB 的 visual sandbox

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main sandbox run ^
  --sequence samples\policy_sequences\simple_safe_sequence.json ^
  --scene bench\sim_robot_arm\simple_joint_move_001\scene.json ^
  --backend mock ^
  --output-root output_reports\sandbox ^
  --metrics-db output_reports\runtime_metrics\runtime_metrics.db ^
  --json
```

生成的 episode 证据：

```text
metadata.json
steps.jsonl
episode_summary.md
clearance_curve.png
trajectory_overview.png
trajectory_overview_data.json
```

### 查询 runtime metrics

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main metrics list-runs ^
  --db output_reports\runtime_metrics\runtime_metrics.db ^
  --json
```

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main metrics show-run ^
  --db output_reports\runtime_metrics\runtime_metrics.db ^
  --episode-id episode_xxx ^
  --json
```

### 诊断命令

诊断回归支持三种 case set：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic regression --case-set smoke --json
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic regression --case-set level2 --json
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic regression --case-set all --json
```

Case set 含义：

| 集合 | 内容 |
|---|---|
| `smoke`（默认） | `simple_safe_sequence` — 管道冒烟测试 |
| `level2` | 3 个 Level-2 复杂安全场景，带 expected contract |
| `all` | smoke + level2 |

Level-2 场景：

- **near_threshold_clearance_sequence**：近阈值安全距离，预期 manual_review。
- **midpoint_collision_sequence**：轨迹中段碰撞，预期 reject。
- **mixed_decision_sequence**：同一序列中同时出现 approve / manual_review / reject。

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic run ^
  --episode-id <episode_id> ^
  --db output_reports\runtime_metrics\runtime_metrics.db ^
  --output-dir output_reports\diagnostics ^
  --json
```

从已有 context 生成报告：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic report ^
  --context output_reports\diagnostics\<episode_id>\context\diagnostic_context.json ^
  --output-dir output_reports\diagnostic_report ^
  --json
```

基于已有诊断证据生成可选诊断分析：

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.main diagnostic analyze ^
  --context output_reports\diagnostics\<episode_id>\context\diagnostic_context.json ^
  --manifest output_reports\diagnostics\<episode_id>\evidence_manifest.json ^
  --report output_reports\diagnostics\<episode_id>\diagnostic_report.md ^
  --output-dir output_reports\diagnostic_analysis ^
  --provider fake ^
  --json
```

该命令使用 deterministic fake analyst 生成 `llm_diagnostic_analysis.json`，不会影响安全决策。

## 下一阶段方向

后续主线将转向 Perception-Aware Safety Fusion：定义感知结果 schema，将人体/障碍物检测结果转换为动态安全约束，与机械臂轨迹安全评估结果进行融合。

## 架构概览

```text
PolicyActionSequence / dataset sample
  -> sandbox run
  -> deterministic SafetyRuntime review
  -> EpisodeRecorder
  -> visual artifacts
  -> runtime metrics DB
  -> diagnostic context
  -> deterministic diagnostic report
  -> evidence_manifest.json
  -> expected-vs-actual contract validation
  -> diagnostic regression summary
  -> optional diagnostic analysis
```

规划中的 Stage 5：

```text
Planned Stage 5: Perception-Aware Safety Fusion
  -> perception_result.json
  -> perception-to-safety constraints
  -> trajectory + perception risk fusion
  -> perception-aware regression cases
```

主要模块：

```text
robot_safety/                 确定性安全模型、轨迹、碰撞、评估、评分
sim/                          backend 抽象、mock backend、PyBullet backend、诊断
robot_runtime/                runtime action、observation、device、sequence、episode recorder/loader
dataset_adapters/             mini_sequence 和本地 LeRobot-style adapters
runtime_db/                   SQLite schema、repository、episode ingest
diagnostic_runtime/           诊断运行时框架
  context/                     确定性诊断上下文包
  tools/                       只读诊断上下文查询层
  report/                      确定性诊断报告生成
  agent/                       fake / DeepSeek diagnostic agent runner
  guardrails/                  输出安全边界检查
  runtime/                     诊断工作流编排与 trace
application/                  review、runtime、sequence、dataset、sandbox、metrics、context services
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

## 项目文档

- [当前状态](docs/project_current_status.md)
- [项目架构](docs/project_architecture.md)
- [核心函数地图](docs/core_function_map.md)
- [Stage 2 后端诊断](docs/stage2_backend_diagnostics.zh-CN.md)
- [Windows PyBullet 环境配置](docs/windows_pybullet_setup.md)
- [面试说明](docs/interview_notes.md)
