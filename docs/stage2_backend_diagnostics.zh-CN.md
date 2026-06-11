# Stage 2 后端诊断

[English version](stage2_backend_diagnostics.md)

## 目的

本文记录 deterministic mock backend 与 PyBullet backend 之间的对比诊断。目标不是证明两个后端完全一致，而是让后端差异足够可见，从而决定下一步工程工作应该做什么。

## 当前后端

### Mock Backend

- 名称：`mock`
- 碰撞方法：`segment_sphere_clearance`
- 模型版本：`mock_geometry_v1`
- 角色：用于回归测试、benchmark 评分和 fallback execution 的确定性基线。

### PyBullet Backend

- 名称：`pybullet`
- 模式：`DIRECT`
- URDF：`assets/robots/mock_realman_6dof/robot.urdf`
- 碰撞方法：`pybullet_closest_points_sphere_collision`
- 保真度：`collision_geometry`
- closest-point 搜索距离：`0.30`
- base collision checking：默认关闭
- 边界：使用 PyBullet closest-point query，在 URDF collision geometry 和球体障碍物 body 之间查询距离。它比 link-frame sampling 保真度更高，但仍然依赖 URDF collision geometry 和 benchmark obstacle modeling。

## Stage 2.5A 之前

Stage 2.4 的 PyBullet backend 使用 `link_position_sphere_clearance`。早期笔记里记录过 `Decision matches: 6/8`，但这个数值使用的是旧的 strict-style match 定义。按当前指标名称重新解释如下：

| 指标 | 数值 |
|---|---:|
| Tasks | 8 |
| Decision matches | 7 |
| Risk matches | 7 |
| Clearance band matches | 6 |
| Attribution matches | 8 |
| Strict matches | 6 |
| Backend errors | 0 |

主要不一致：

| Task | Mock | PyBullet | 诊断 |
|---|---|---|---|
| `mid_trajectory_collision_001` | `reject`, high, min clearance `-0.064573` | `manual_review`, medium, min clearance `0.089615` | `decision_disagreement` |

可能原因：link-frame position sampling 可能漏掉 link body 沿线发生的重叠。

## Stage 2.5A 之后

由以下命令生成：

```powershell
python -m cli.compare_backends `
  --bench bench\sim_robot_arm `
  --backends mock pybullet `
  --output-json output_reports\backend_comparison.json `
  --output-md output_reports\backend_comparison.md
```

| 指标 | 数值 |
|---|---:|
| Tasks | 8 |
| Decision matches | 8 |
| Risk matches | 8 |
| Clearance band matches | 6 |
| Attribution matches | 7 |
| Strict matches | 6 |
| Backend errors | 0 |

当前 PyBullet backend 会报告：

```json
{
  "collision_method": "pybullet_closest_points_sphere_collision",
  "fidelity": "collision_geometry",
  "closest_point_search_distance": 0.3,
  "include_base_collision": false
}
```

## 一致案例

| Task | Decision | 诊断 |
|---|---|---|
| `invalid_command_001` | `reject` | `consistent_reject` |
| `joint_limit_violation_001` | `reject` | `consistent_reject` |
| `long_motion_delta_risk_001` | `manual_review` | `consistent_manual_review` |
| `near_miss_clearance_001` | `manual_review` | `consistent_manual_review` |
| `obstacle_collision_001` | `reject` | `consistent_reject` |
| `simple_joint_move_001` | `approve` | `consistent_safe` |

这些案例说明，在 closest-point upgrade 之后，backend abstraction、logging、reporting 和 benchmark comparison pipeline 仍然稳定。

## 剩余差异

### `mid_trajectory_collision_001`

| Backend | Decision | Risk | Min Clearance | Closest Link | Closest Obstacle | Worst Step | Violations |
|---|---|---|---:|---|---|---:|---|
| `mock` | `reject` | `high` | -0.064573 | `link_4` | `sphere_mid` | 10 | `environment_collision` |
| `pybullet` | `reject` | `high` | 0.045865 | `link_3` | `sphere_mid` | 5 | `clearance_violation` |

诊断：`clearance_threshold_disagreement`

Stage 2.5A 将该案例从 decision/risk mismatch 改善为一致的 high-risk rejection。剩余差异是几何层面的：mock model 报告 `link_4` 发生 penetration，而 PyBullet 报告 `link_3` 为正间隙，但低于 hard-threshold clearance。

工程含义：安全决策已经对齐，但 mock segment geometry 和 URDF collision geometry 之间的 geometry attribution 与精确 clearance 仍未标定。

### `multi_obstacle_clearance_001`

| Backend | Decision | Risk | Min Clearance | Closest Link | Closest Obstacle | Worst Step | Diagnosis |
|---|---|---|---:|---|---|---:|---|
| `mock` | `approve` | `low` | 0.095 | `link_3` | `sphere_near` | 0 | baseline |
| `pybullet` | `approve` | `low` | 0.100 | `link_3` | `sphere_near` | 4 | `clearance_threshold_disagreement` |

两个后端都以 low risk approve 该指令。剩余 mismatch 是 manual-review 边界附近的 threshold-band artifact。

工程含义：这不阻碍 PyBullet 作为 diagnostic backend 使用。它说明 exact clearance value 目前还不应该被当作跨后端已标定的指标。

## Stage 2.5A 结论

Stage 2.5A 完成了预期的 backend fidelity upgrade：

- PyBullet 现在默认使用 URDF collision geometry closest-point checking；
- 之前的 link-position sampling 方法仍在内部保留；
- metadata 会记录 collision method、fidelity、checked links 和 search distance；
- PyBullet smoke benchmark 可完成全部 8 个任务；
- mock benchmark 仍通过全部 8 个任务；
- backend comparison 有 0 个 backend errors；
- final decision matches 从 7/8 提升到 8/8；
- risk matches 从 7/8 提升到 8/8。

Strict matches 仍然是 6/8，因为 `mid_trajectory_collision_001` 和 `multi_obstacle_clearance_001` 上仍存在 clearance-band 和 attribution 差异。

## Stage 2.5B 几何诊断

Stage 2.5B 为 PyBullet 任务增加了结构化几何诊断：

```powershell
python -m cli.diagnose_backend_geometry `
  --task bench\sim_robot_arm\mid_trajectory_collision_001 `
  --output-json output_reports\mid_trajectory_geometry_diagnostics.json
```

诊断输出会记录：

- checked links；
- 每个 step 的 joint values；
- 每个 step 的 PyBullet link poses；
- closest-point observations；
- worst robot-link / obstacle pair。

对于 `mid_trajectory_collision_001`，诊断得到的 worst pair 是：

| 字段 | 数值 |
|---|---|
| Step | 5 |
| Robot link | `link_3` |
| Obstacle | `sphere_mid` |
| Clearance | 0.045865 |
| Position on robot | `[0.585978, 0.078356, 0.167939]` |
| Position on obstacle | `[0.583853, 0.099532, 0.208567]` |
| Normal on obstacle | `[0.046325, -0.461707, -0.885822]` |

Checked links：

```text
link_1, link_2, link_3, link_4, link_5, link_6
```

在 worst step，PyBullet 报告以下相关 link poses：

| Link | Position | Orientation |
|---|---|---|
| `link_3` | `[0.456111, 0.045764, 0.148053]` | `[0.0, 0.0, 0.049979, 0.99875]` |
| `link_4` | `[0.694912, 0.069724, 0.148053]` | `[0.0, 0.0, 0.049979, 0.99875]` |

对于 `multi_obstacle_clearance_001`，诊断得到的 worst pair 是：

| 字段 | 数值 |
|---|---|
| Step | 0 |
| Robot link | `link_3` |
| Obstacle | `sphere_near` |
| Clearance | 0.100 |

解释：

- Stage 2.5B 确认 PyBullet closest-point path 能产出结构化、可检查的几何数据。
- `mid_trajectory_collision_001` 的差异已经不再是 backend execution 或 missing-closest-point 问题。PyBullet 在 `link_3` 上看到 hard-threshold clearance 下的最近几何，而 mock segment model 在 `link_4` 上报告 penetration。
- `multi_obstacle_clearance_001` 的差异仍然是 `0.10` 附近的 threshold-boundary issue。

## Stage 2.5C URDF 标定

Stage 2.5C 增加了 URDF-vs-mock calibration report：

```powershell
python -m cli.calibrate_urdf_geometry `
  --task bench\sim_robot_arm\mid_trajectory_collision_001 `
  --output-json output_reports\mid_trajectory_urdf_calibration.json
```

对于 `mid_trajectory_collision_001`，标定摘要如下：

| 字段 | 数值 |
|---|---|
| PyBullet worst step | 5 |
| PyBullet closest | `link_3`, `sphere_mid`, clearance `0.045865` |
| Mock at PyBullet worst step | `link_3`, `sphere_mid`, clearance `0.002415` |
| Mock overall worst | step `10`, `link_4`, `sphere_mid`, clearance `-0.064573` |
| Conclusion | `kinematic_model_mismatch` |

相关 link calibration：

| Link | URDF Length | Mock Length | Length Delta | Endpoint Alignment Error |
|---|---:|---:|---:|---:|
| `link_3` | 0.28 | 0.28 | 0.0 | 0.153891 |
| `link_4` | 0.20 | 0.20 | 0.0 | 0.118669 |

解释：

- `link_3` 和 `link_4` 的 URDF collision lengths 与 mock link lengths 一致。
- 剩余差异不是简单的 collision-size mismatch。
- 在 PyBullet 的 worst step，两个模型都认为 `link_3` 最接近 `sphere_mid`，但 mock clearance 更紧。
- 在完整轨迹上，mock backend 的 overall worst case 出现在更晚的 step 10，且位于 `link_4`。
- 这指向 kinematic-model mismatch：mock FK 对后续关节使用简化 yaw/pitch 更新，而 URDF 有显式 joint axes 和 x-axis wrist rotations。

## Stage 2.5 总结

对当前项目范围而言，Stage 2.5 已完成：

- Stage 2.5A 将 PyBullet 从 link-frame sampling 升级为 collision-geometry closest-point checking。
- Stage 2.5B 增加了可检查的 PyBullet geometry diagnostics。
- Stage 2.5C 增加了 URDF-vs-mock calibration reporting。
- 剩余差异可以解释为 mock-vs-URDF model differences，而不是 backend runtime failures。

推荐下一步：

```text
Stage 2.6: Backend-specific expectations and/or visual replay
```

推荐优先级：

1. 如果 PyBullet scoring 需要独立于 mock scoring 进行衡量，则增加 backend-specific benchmark expectations。
2. 在 expectations 清晰之后再增加 visual replay，这样截图展示的是已知 backend behavior，而不是尚未解决的 calibration ambiguity。
