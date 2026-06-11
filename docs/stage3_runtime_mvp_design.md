# Stage 3 Runtime MVP Design

## 1. Goal

Stage 3 MVP upgrades RobotArmSafetyReviewer from an offline JSON command reviewer into a minimal robot action safety runtime.

Current Stage 2 flow:

```text
scene.json + command.json
  -> safety review
  -> log / report / benchmark
```

Stage 3 MVP flow:

```text
RobotObservation + RobotAction
  -> SafetyRuntime
  -> existing safety review
  -> conditional execution
  -> episode log
```

The phrase **LeRobot-compatible** does not mean depending on LeRobot or recreating LeRobot. It means this project borrows the observation/action interface idea and inserts a deterministic safety runtime between a policy/teleop/agent action source and robot execution.

## 2. Scope

Stage 3 MVP does:

- define a small runtime data model: `RobotObservation`, `RobotAction`, `RuntimeStepResult`;
- define a `RobotDeviceAdapter` protocol for observation and action execution;
- wrap the existing mock robot adapter as `MockRealManDevice`;
- define `ActionSource` and implement `ReplayActionSource` from existing `command.json`;
- define `SceneProvider` and implement `StaticSceneProvider` from existing `scene.json`;
- implement `SafetyRuntime.step()`;
- implement `EpisodeRecorder`;
- add a demo CLI for safe, manual-review, and rejected tasks;
- add tests for the action runtime loop.

Stage 3 MVP does not:

- connect to the real RealMan SDK;
- install or depend on LeRobot;
- implement a real LLM Agent;
- implement vision input;
- implement teleoperation;
- implement path planning or obstacle avoidance;
- implement self-collision or dynamics;
- replace the existing gateway, benchmark, scorer, report, or diagnostics pipeline;
- implement a full imitation-learning dataset format.

## 3. Core Components

| Component | File | Responsibility |
|---|---|---|
| Runtime types | `robot_runtime/types.py` | Define `RobotObservation`, `RobotAction`, and `RuntimeStepResult`. |
| Device adapter | `robot_runtime/device.py` | Define a LeRobot-style internal protocol for `get_observation` and `send_action`. |
| Mock device | `robot_runtime/adapters/mock_realman_device.py` | Use existing mock execution behavior to validate runtime safety gating without hardware. |
| Action source | `robot_runtime/action_source.py` | Define action proposal interface and `ReplayActionSource`. |
| Scene provider | `robot_runtime/scene_provider.py` | Make scene source explicit; MVP uses `StaticSceneProvider`. |
| Safety runtime | `robot_runtime/safety_runtime.py` | Convert observation/action to `JointCommand`, run safety review, conditionally execute. |
| Episode recorder | `robot_runtime/episode_recorder.py` | Record observation, proposed action, safety result, execution result, and backend metadata. |
| Demo CLI | `cli/run_runtime_demo.py` | Run one benchmark task through the runtime loop and write an episode log. |

## 4. Data Types

Keep the first version intentionally small.

```python
@dataclass(frozen=True)
class RobotObservation:
    robot_id: str
    joint_positions: tuple[float, ...]
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)
```

```python
@dataclass(frozen=True)
class RobotAction:
    action_type: str
    target_joints: tuple[float, ...]
    speed: float = 0.1
    source: str = "replay"
    metadata: dict[str, Any] = field(default_factory=dict)
```

```python
@dataclass(frozen=True)
class RuntimeStepResult:
    step_id: str
    observation: RobotObservation
    proposed_action: RobotAction
    safety_result: SafetyResult
    backend_metadata: dict[str, Any]
    executed: bool
    sent_action: RobotAction | None
    blocked_reason: str | None
    episode_step_path: Path | None = None
```

Future fields such as images, end-effector pose, joint velocity, torque, and camera metadata should be added only after the MVP loop is stable.

## 5. Interfaces

### RobotDeviceAdapter

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

This is an internal project interface. It may later wrap a LeRobot `Robot`, PyBullet device, serial device, or vendor SDK.

### ActionSource

```python
class ActionSource(Protocol):
    name: str

    def propose_action(self, observation: RobotObservation) -> RobotAction:
        ...
```

MVP implementation:

- `ReplayActionSource(command_path)`: reads an existing benchmark `command.json` and proposes a `RobotAction`.

Future implementations:

- `TeleopActionSource`;
- `PolicyActionSource`;
- `AgentActionSource`.

All action sources produce proposals only. They must not call `send_action`.

### SceneProvider

```python
class SceneProvider(Protocol):
    name: str

    def get_scene(self, observation: RobotObservation) -> Scene:
        ...
```

MVP implementation:

- `StaticSceneProvider(scene_path)`: reads an existing benchmark `scene.json` and returns it for every step.

This small interface is important because the existing safety reviewer requires `Scene + JointCommand`, while the runtime starts from `RobotObservation + RobotAction`.

## 6. SafetyRuntime.step()

`SafetyRuntime.step()` is the main value of Stage 3 MVP.

```text
RobotDeviceAdapter.get_observation()
  -> ActionSource.propose_action(observation)
  -> SceneProvider.get_scene(observation)
  -> action_to_joint_command(observation, action)
  -> evaluate_joint_command_with_metadata(scene, command, backend)
  -> if approve: RobotDeviceAdapter.send_action(action)
  -> else: block
  -> EpisodeRecorder.record_step(...)
  -> RuntimeStepResult
```

Execution rule:

| Decision | Runtime behavior |
|---|---|
| `approve` | Call `send_action`; record `executed=true`. |
| `manual_review` | Do not call `send_action`; record `executed=false`, `blocked_reason=manual_review_required`. |
| `reject` | Do not call `send_action`; record `executed=false`, `blocked_reason=rejected_by_safety_gate`. |

Conversion rule:

```text
RobotObservation.joint_positions -> JointCommand.current_joints
RobotAction.target_joints        -> JointCommand.target_joints
RobotAction.speed                -> JointCommand.speed
RobotAction.source               -> JointCommand.source
```

The resulting `JointCommand.command_id` should be deterministic enough for logs, for example:

```text
runtime_<step_id>
```

## 7. EpisodeRecorder

The MVP recorder should create:

```text
episode_dir/
  metadata.json
  steps.jsonl
```

`metadata.json` records episode-level context:

```json
{
  "schema_version": "stage3.runtime_episode.v1",
  "episode_id": "episode_YYYYMMDD_HHMMSS_xxxxxxxx",
  "robot": "mock_realman_device",
  "action_source": "replay",
  "scene_provider": "static_scene",
  "backend": "mock"
}
```

Each `steps.jsonl` line records one runtime step:

```json
{
  "step_id": "step_000001",
  "observation": {
    "robot_id": "mock_realman_6dof",
    "joint_positions": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    "timestamp": "2026-06-11T10:00:00Z"
  },
  "proposed_action": {
    "action_type": "joint_move",
    "target_joints": [0.1, 0.2, 0.0, 0.0, 0.0, 0.0],
    "speed": 0.1,
    "source": "replay"
  },
  "safety_result": {
    "decision": "approve",
    "risk_level": "low"
  },
  "backend_metadata": {
    "name": "mock"
  },
  "executed": true,
  "sent_action": {
    "action_type": "joint_move",
    "target_joints": [0.1, 0.2, 0.0, 0.0, 0.0, 0.0]
  },
  "blocked_reason": null
}
```

## 8. Demo Tasks

The demo CLI should support at least these benchmark tasks:

| Task | Expected decision | Expected execution |
|---|---|---|
| `simple_joint_move_001` | `approve` | `send_action` called; `executed=true`. |
| `near_miss_clearance_001` | `manual_review` | `send_action` not called; `executed=false`. |
| `obstacle_collision_001` | `reject` | `send_action` not called; `executed=false`. |

Example command:

```powershell
python -m cli.run_runtime_demo `
  --task bench\sim_robot_arm\simple_joint_move_001 `
  --backend mock `
  --episode-dir output_reports\runtime_demo
```

## 9. Tests

Acceptance tests:

1. `RobotAction` and `RobotObservation` serialize to dicts.
2. `MockRealManDevice.connect()` enables `get_observation()`.
3. `MockRealManDevice.send_action()` raises before `connect()`.
4. `ReplayActionSource` reads `command.json` and returns `RobotAction`.
5. `StaticSceneProvider` reads `scene.json` and returns `Scene`.
6. `SafetyRuntime` calls `send_action` for approved actions.
7. `SafetyRuntime` blocks rejected actions.
8. `SafetyRuntime` blocks manual-review actions.
9. `EpisodeRecorder` writes `metadata.json` and `steps.jsonl`.
10. Runtime demo CLI runs safe, manual-review, and rejected tasks.

Suggested test files:

```text
tests/test_stage3_runtime_types.py
tests/test_stage3_mock_realman_device.py
tests/test_stage3_replay_action_source.py
tests/test_stage3_scene_provider.py
tests/test_stage3_safety_runtime.py
tests/test_stage3_episode_recorder.py
tests/test_stage3_runtime_demo_cli.py
```

## 10. AI / Agent Boundary

Stage 3 MVP does not implement an Agent.

It prepares the correct boundary:

```text
ReplayActionSource now
TeleopActionSource later
PolicyActionSource later
AgentActionSource later
```

Every source must produce a `RobotAction` proposal. Every proposal must pass through `SafetyRuntime`. No Agent should directly call `RobotDeviceAdapter.send_action`.

This keeps the project aligned with its safety value:

```text
AI proposes.
Deterministic safety runtime decides.
Robot executes only approved actions.
Episode logs preserve evidence.
```

## 11. Implementation Order

Recommended order:

1. Review this design document and confirm scope.
2. Write `docs/plans/stage3_runtime_mvp.md`.
3. Add failing tests for runtime types, device, action source, scene provider, runtime, recorder, and CLI.
4. Implement `robot_runtime/types.py`.
5. Implement `robot_runtime/device.py` and `robot_runtime/adapters/mock_realman_device.py`.
6. Implement `robot_runtime/action_source.py`.
7. Implement `robot_runtime/scene_provider.py`.
8. Implement `robot_runtime/safety_runtime.py`.
9. Implement `robot_runtime/episode_recorder.py`.
10. Implement `cli/run_runtime_demo.py`.
11. Run focused Stage 3 tests.
12. Run full `pytest`.
13. Run safe, manual-review, and rejected runtime demos.

## 12. Resume / Interview Value

This stage lets the project be described as:

```text
Built a LeRobot-compatible robot action safety runtime that inserts a deterministic safety gate between policy/agent action proposals and robot execution. The runtime converts observation-action proposals into existing safety-review commands, blocks unsafe actions, conditionally executes approved actions, and records episode-level audit logs for diagnostics.
```

Chinese version:

```text
我把原来的离线机械臂安全审查器升级成了一个 LeRobot-compatible safety runtime。它位于 policy/Agent action 和 robot execution 之间，把 action proposal 转成已有的 JointCommand 安全审查流程，只有 approve 才能进入 send_action，manual_review/reject 都会被阻断，并记录 episode 级别的审计日志。
```
