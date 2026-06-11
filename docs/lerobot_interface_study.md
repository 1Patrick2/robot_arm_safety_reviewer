# LeRobot Interface Study

## 1. Purpose

This document defines how RobotArmSafetyReviewer should relate to LeRobot in future Stage 3 work.

The goal is not to copy LeRobot or build a lower-quality replacement. LeRobot already provides an end-to-end robot learning stack: robot interfaces, hardware integration, teleoperation, datasets, policy training, inference, and evaluation.

The useful direction for this project is narrower:

```text
LeRobot-style policy / teleop / agent action
  -> RobotArmSafetyReviewer safety runtime
  -> deterministic review
  -> approve / manual_review / reject
  -> conditional execution
  -> episode log and diagnostics
```

In other words, the intended Stage 3 direction is a **LeRobot-compatible robot safety runtime**, or a safety interposer between an action-producing system and the final robot `send_action` call.

## 2. What LeRobot Already Does

LeRobot is a robot learning ecosystem for real-world robotics in PyTorch. Its public docs describe it as a library for models, datasets, and tools for real-world robotics, with a goal of lowering the barrier to robotics work through shared datasets and pretrained models.

The current LeRobot README and docs emphasize:

- hardware-agnostic robot control interfaces;
- supported robots and teleoperation devices;
- dataset collection, storage, visualization, and sharing;
- policy training for imitation learning, reinforcement learning, and VLA-style models;
- simulation and benchmark support;
- extension mechanisms for custom hardware.

This means RobotArmSafetyReviewer should not duplicate:

- LeRobot's dataset format;
- LeRobot's training scripts;
- LeRobot's policy implementations;
- LeRobot's teleoperation stack;
- LeRobot's supported hardware ecosystem;
- LeRobot's general robot-learning CLI.

## 3. The LeRobot Robot Interface

LeRobot's `Robot` abstraction defines a standard interface that custom physical robots should implement to work with the LeRobot toolchain.

Important interface concepts:

- `observation_features`: describes the structure of observations returned by `get_observation`.
- `action_features`: describes the action structure expected by `send_action`.
- `is_connected`: reports whether hardware communication is active.
- `connect(calibrate=True)`: establishes robot communication and optionally calibrates.
- `is_calibrated`: reports whether required calibration is available.
- `calibrate()`: collects or loads calibration data when needed.
- `configure()`: applies motor/control/camera configuration.
- `get_observation()`: reads current robot state and sensor data.
- `send_action(action)`: sends an action command and returns the action actually sent.
- `disconnect()`: releases hardware resources.

LeRobot observations and actions are dictionary-like structures. In the current codebase, `RobotObservation` and `RobotAction` are typed as `dict[str, Any]`, which makes feature schemas important: tools need to know what keys and shapes to expect.

## 4. Where This Project Fits

RobotArmSafetyReviewer should sit between action proposal and action execution.

LeRobot-style loop:

```text
observation = robot.get_observation()
action = policy.select_action(observation)
robot.send_action(action)
```

RobotArmSafetyReviewer Stage 3 loop:

```text
observation = robot.get_observation()
action = policy_or_agent.propose_action(observation)
review = safety_runtime.review_action(observation, action)

if review.decision == "approve":
    robot.send_action(action)
else:
    block execution and write an episode log
```

This keeps LeRobot's role and this project's role separate:

| Layer | Responsibility |
|---|---|
| LeRobot | Robot learning stack: robot abstraction, datasets, teleoperation, training, inference, evaluation. |
| RobotArmSafetyReviewer | Runtime safety interposer: review proposed actions, block unsafe execution, log evidence, explain diagnostics. |

## 5. Why Not Directly Use LeRobot

Use LeRobot directly when the goal is:

- collecting imitation-learning data;
- training ACT / Diffusion Policy / SmolVLA-style policies;
- using officially supported low-cost robots;
- running standard teleoperation, record, replay, train, or eval workflows;
- integrating with Hugging Face robot-learning datasets.

RobotArmSafetyReviewer remains meaningful because it solves a different problem:

- deterministic joint-space trajectory safety review;
- mock/PyBullet backend comparison;
- clearance, closest link, closest obstacle, and worst-step diagnostics;
- `approve / manual_review / reject` safety decisions;
- rejected-action audit logs;
- future episode-level diagnostics for policy or agent behavior.

The concise positioning is:

```text
Do not replace LeRobot.
Wrap or interpose around LeRobot-style robot/action flows.
Let deterministic safety tools decide whether a proposed action may execute.
```

## 6. Proposed Stage 3 Architecture

The next stage should be incremental. Do not build a broad LeRobot clone.

Recommended roadmap:

```text
Stage 3.0: LeRobot interface study and compatibility design
Stage 3.1: RobotDeviceAdapter / SafeRobotDevice internal interface
Stage 3.2: SafetyRuntime action interposer
Stage 3.3: EpisodeRecorder
Stage 3.4: ActionSource and Agent Diagnostic Tool Layer
Stage 3.5: PyBulletRobotDevice or SerialRobotDevice
```

### Stage 3.1: RobotDeviceAdapter

Use a name that avoids implying a replacement for LeRobot's `Robot` class.

Candidate names:

- `RobotDeviceAdapter`
- `SafeRobotDevice`

The adapter should be internal to this project. Later, it can wrap:

- the current `MockRealMan6DoFAdapter`;
- a PyBullet robot device;
- a serial/SDK robot device;
- a LeRobot `Robot` instance.

Sketch:

```python
class RobotDeviceAdapter(Protocol):
    name: str

    @property
    def observation_features(self) -> dict:
        ...

    @property
    def action_features(self) -> dict:
        ...

    @property
    def is_connected(self) -> bool:
        ...

    def connect(self, calibrate: bool = True) -> None:
        ...

    def get_observation(self) -> RobotObservation:
        ...

    def send_action(self, action: RobotAction) -> RobotAction:
        ...

    def disconnect(self) -> None:
        ...
```

### Stage 3.2: SafetyRuntime

This is the core value layer.

`SafetyRuntime` should convert observation/action state into the project's existing `Scene`, `JointCommand`, and `SafetyResult` flow.

Sketch:

```python
class SafetyRuntime:
    def step(self, action: RobotAction) -> RuntimeStepResult:
        observation = self.robot.get_observation()
        scene = self.scene_provider.get_scene(observation)
        command = action_to_joint_command(observation, action)

        outcome = evaluate_joint_command_with_metadata(scene, command, backend=self.backend)

        if outcome.safety_result.decision == "approve":
            sent_action = self.robot.send_action(action)
            executed = True
        else:
            sent_action = None
            executed = False

        self.recorder.record_step(...)
        return RuntimeStepResult(...)
```

The important boundary:

```text
Agent or policy may propose actions.
Only SafetyRuntime may decide whether the action reaches send_action.
```

### Stage 3.3: EpisodeRecorder

Episode-level logs should record every proposed action, whether it was executed, and the safety evidence.

Minimal step record:

```json
{
  "step_id": "step_000001",
  "timestamp": "2026-06-11T10:00:00Z",
  "observation": {
    "joint_positions": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
  },
  "proposed_action": {
    "action_type": "joint_move",
    "target_joints": [0.1, 0.2, 0.0, 0.0, 0.0, 0.0]
  },
  "safety_result": {
    "decision": "manual_review",
    "risk_level": "medium",
    "min_clearance": 0.06
  },
  "executed": false,
  "sent_action": null,
  "backend_metadata": {
    "name": "pybullet"
  }
}
```

This creates data for later questions:

- Which actions did a policy propose?
- Which actions were blocked?
- Are near misses concentrated in the same workspace region?
- Where do mock and PyBullet disagree?
- What unsafe pattern should an Agent diagnostic assistant explain?

### Stage 3.4: ActionSource And Agent Diagnostics

An action source proposes actions. It does not execute them.

```python
class ActionSource(Protocol):
    name: str

    def propose_action(self, observation: RobotObservation) -> RobotAction:
        ...
```

Initial implementations:

- `ReplayActionSource`: replays actions from existing `command.json` or episode logs.
- `RulePolicyActionSource`: produces simple deterministic test actions.
- `AgentActionSource`: asks an LLM for a structured action proposal.

Agent output should be a proposal:

```json
{
  "action_type": "joint_move",
  "target_joints": [0.1, 0.2, 0.0, 0.0, 0.0, 0.0],
  "speed": 0.1,
  "reason": "Move to inspection pose"
}
```

The Agent may later use tools such as:

- `review_runtime_action`;
- `summarize_episode`;
- `explain_rejection`;
- `compare_backends`;
- `diagnose_geometry`;
- `calibrate_urdf`;
- `generate_report`.

The Agent must not:

- directly call `robot.send_action`;
- override safety decisions;
- silently change thresholds before execution.

## 7. Minimum Stage 3 MVP

The smallest useful Stage 3 loop is:

```text
RobotDeviceAdapter
MockRealManDevice
ReplayActionSource
SafetyRuntime.step()
EpisodeRecorder
```

Demo flow:

```text
command.json
  -> ReplayActionSource proposes RobotAction
  -> SafetyRuntime reads observation
  -> action_to_joint_command builds JointCommand
  -> evaluate_joint_command_with_metadata reviews it
  -> approve sends action
  -> manual_review/reject blocks action
  -> EpisodeRecorder writes step log
```

This is enough to show that the project has moved from offline JSON review to a robot action execution loop without pretending to be a full LeRobot replacement.

## 8. Interview Positioning

Recommended phrasing:

```text
I referenced LeRobot's Robot abstraction, but I did not try to recreate LeRobot.
LeRobot solves robot learning, data, teleoperation, and policy deployment.
My project adds a deterministic safety runtime between policy/agent actions and robot execution.
Only approved actions can reach send_action; blocked actions are logged with diagnostics.
```

Chinese version:

```text
我没有复刻 LeRobot，而是参考它的 observation/action 接口边界，把现有安全审查器升级成 LeRobot-compatible safety runtime。
LeRobot 负责机器人学习生态和硬件接口；我的项目负责在 policy/Agent action 和 robot.send_action 之间加入 deterministic safety gate、diagnostics 和 episode logging。
```

## 9. References

- Hugging Face LeRobot documentation: https://huggingface.co/docs/lerobot
- LeRobot GitHub README: https://github.com/huggingface/lerobot
- LeRobot custom hardware integration guide: https://huggingface.co/docs/lerobot/integrate_hardware
- LeRobot `Robot` base class: https://github.com/huggingface/lerobot/blob/main/src/lerobot/robots/robot.py
- LeRobot paper: https://arxiv.org/abs/2602.22818
