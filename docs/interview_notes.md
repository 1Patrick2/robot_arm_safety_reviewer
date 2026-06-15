# Interview Notes

## 30-Second Introduction

RobotArmSafetyReviewer is a simulation-first safety gate for 6-DOF robot-arm joint-space commands. It checks a candidate `current_joints -> target_joints` command before execution using deterministic rules, trajectory interpolation, joint-limit checks, collision/clearance checks, and backend simulation. The output is `approve`, `manual_review`, or `reject`, with replayable logs, benchmark scoring, reports, and PyBullet diagnostics.

## 中文 30 秒介绍

RobotArmSafetyReviewer 是一个面向 6 自由度机械臂关节空间指令的执行前安全审查框架。输入结构化 `scene.json` 和 `current_joints -> target_joints` 候选指令后，系统会做轨迹插值、关节限位检查、碰撞与 clearance 检查，并通过 mock 或 PyBullet 后端输出 `approve`、`manual_review` 或 `reject`。项目还包含可回放日志、benchmark/scorer、Markdown 报告和 mock-vs-PyBullet 诊断，用来保证安全审查结果可复现、可量化、可解释。

## 2-Minute Introduction

This project focuses on the safety-review layer before robot execution. The input is a structured scene and a joint-space command. The system interpolates the full joint trajectory, checks joint limits and motion delta, then sends the trajectory to a simulation backend for collision and clearance review.

The first backend is a deterministic mock geometry backend, which is fast and stable for regression tests and benchmark scoring. The second backend is a PyBullet URDF backend, which replays the robot model in PyBullet and uses closest-point collision queries for higher-fidelity diagnostics.

The gateway has two modes. `review_only` only audits the command and writes a log. `execute_if_safe` runs the same audit first, and only approved commands are passed to the robot adapter. Rejected or manual-review commands never reach execution.

Around the safety gate, I built a benchmark/scorer/replay/report loop. This makes the project measurable: every task has expected behavior, every review produces a structured log, logs can be replayed, and reports can be generated for human inspection.

The key design principle is that deterministic safety tools make the final safety decision. LLMs or agents can later help explain logs, choose diagnostics, or generate reports, but they should not directly decide whether a robot command is safe.

## Biggest Technical Challenge

The hardest part was handling disagreement between the simplified mock backend and the PyBullet URDF backend.

The mock backend uses simplified kinematic segments and sphere clearance. PyBullet uses URDF collision geometry and closest-point queries. They can agree on the final decision while disagreeing on exact clearance, closest link, or worst step.

Instead of forcing PyBullet to match the mock model, the project separates comparison metrics:

- decision match;
- risk match;
- clearance-band match;
- attribution match;
- strict match.

This makes backend disagreement inspectable rather than hidden.

## Why Backend Abstraction

The evaluator should not know whether collision checking comes from mock geometry, PyBullet, or a future simulator.

`SimulationBackend` keeps the evaluator stable:

- mock backend is used for deterministic regression;
- PyBullet backend is used for higher-fidelity diagnostics;
- future backends can be added without changing the safety-result schema or gateway behavior.

This also made it possible to run backend comparison and calibration as first-class tools.

## Why Benchmark And Scorer

Safety code needs repeatable evidence, not only manual demos.

The benchmark layer provides structured tasks such as safe movement, joint limit violation, initial collision, mid-trajectory collision, near miss, large motion delta, multi-obstacle clearance, and invalid command.

The scorer checks whether each task produced the expected decision, risk, violations, and execution behavior. That gives the project quantitative regression signals and makes it easier to explain progress in a resume or interview.

## Why Not Let GPT Decide Safety

The project deliberately does not use an LLM as the final safety judge.

Robot safety decisions should come from deterministic tools that are inspectable, replayable, and testable. An LLM can be useful later for:

- selecting which diagnostic command to run;
- explaining backend comparison results;
- summarizing logs;
- generating human-readable reports.

But the final `approve/manual_review/reject` decision must come from deterministic safety review logic.

## Follow-Up: Why Not Build Planning / Obstacle Avoidance / MoveIt

This project deliberately focuses on the pre-execution safety gate rather than motion planning.

A planner answers: "How should the robot move to reach the target while avoiding obstacles?"

This project answers a narrower question: "Given this candidate joint-space command, is it safe enough to execute?"

That boundary keeps the system testable and easier to audit. A planner such as MoveIt could become an upstream command generator later, but RobotArmSafetyReviewer would still be useful as a downstream reviewer that checks the generated command, records evidence, and blocks unsafe execution.

中文回答可以这样说：

这个项目当前不是为了替代 MoveIt 或实现自动绕障，而是专注在更靠近执行边界的一层：候选指令已经给定后，系统判断它能不能执行。这样做的好处是边界清楚、结果可复现、日志可审计，也方便后续接入不同上游，比如人工指令、规划器或者 Agent。即使未来接入 MoveIt，这个 safety reviewer 也可以作为执行前最后一道审查门。

## Current Project Boundary

Implemented:

- joint-space safety review;
- linear trajectory interpolation;
- joint limit checks;
- obstacle collision and clearance checks;
- deterministic mock backend;
- PyBullet URDF backend;
- execution gate;
- replayable logs;
- benchmark/scorer/replay/report loop;
- backend comparison;
- geometry diagnostics;
- URDF-vs-mock calibration.

Not implemented:

- automatic path planning;
- obstacle avoidance;
- Cartesian IK;
- self-collision;
- workspace boundary;
- dynamics, speed, or acceleration constraints;
- real RealMan SDK execution;
- ROS2 / MoveIt integration;
- VLA or learned policy.

## Future Plan

Near-term Stage 2.6:

- keep project docs clear and interview-ready;
- maintain the current benchmark and diagnostics loop;
- clean up small technical debt such as explicit backend metadata return values;
- avoid adding large features before the project story is clear.

Stage 3.1:

- add a unified CLI entry point such as `python -m cli.main review|execute|benchmark|compare|diagnose|calibrate`.

Stage 3.2:

- wrap existing commands as agent-ready tools with explicit input/output schemas.

Stage 3.3:

- build a natural-language assistant that can call deterministic tools to explain logs and diagnostics, while leaving the safety decision to the existing rule-based reviewer.

## Resume-Ready Phrases

- Built a simulation-first robot-arm safety gate for 6-DOF joint-space commands, producing deterministic `approve/manual_review/reject` decisions before execution.
- Designed a benchmark/scorer/replay/report loop covering 8 structured safety tasks, including joint-limit violation, initial collision, mid-trajectory collision, near miss, and invalid command.
- Added backend abstraction with deterministic mock geometry and PyBullet URDF closest-point collision diagnostics.
- Implemented mock-vs-PyBullet comparison metrics for decision, risk, clearance band, attribution, and strict match, making simulation disagreement measurable.
- Enforced a safety boundary where only approved commands can reach the robot adapter execution layer.
