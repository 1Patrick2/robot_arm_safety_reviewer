# Stage 3 Runtime MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the smallest LeRobot-compatible robot action safety runtime that turns action proposals into reviewed, conditionally executed, episode-logged robot steps.

**Architecture:** Add a new `robot_runtime/` package above the existing safety reviewer. Runtime components convert `RobotObservation + RobotAction` into the existing `Scene + JointCommand` review flow, call `evaluate_joint_command_with_metadata`, execute only approved actions, and record every step into an episode log.

**Tech Stack:** Python dataclasses, Protocol interfaces, existing `robot_safety` models/evaluator, existing `robots.MockRealMan6DoFAdapter`, pytest, JSON/JSONL logs, current conda environment at `D:\miniforge3\envs\robotarm-pybullet\python.exe`.

---

## File Structure

Create:

- `robot_runtime/__init__.py`: public runtime package exports.
- `robot_runtime/types.py`: `RobotObservation`, `RobotAction`, `RuntimeStepResult`, serialization helpers.
- `robot_runtime/device.py`: `RobotDeviceAdapter` protocol.
- `robot_runtime/adapters/__init__.py`: adapter package exports.
- `robot_runtime/adapters/mock_realman_device.py`: LeRobot-style wrapper around `MockRealMan6DoFAdapter`.
- `robot_runtime/action_source.py`: `ActionSource` protocol and `ReplayActionSource`.
- `robot_runtime/scene_provider.py`: `SceneProvider` protocol and `StaticSceneProvider`.
- `robot_runtime/safety_runtime.py`: `action_to_joint_command`, `SafetyRuntime`.
- `robot_runtime/episode_recorder.py`: `EpisodeRecorder`.
- `cli/run_runtime_demo.py`: demo CLI for one benchmark task.
- `tests/test_stage3_runtime_types.py`
- `tests/test_stage3_mock_realman_device.py`
- `tests/test_stage3_replay_action_source.py`
- `tests/test_stage3_scene_provider.py`
- `tests/test_stage3_safety_runtime.py`
- `tests/test_stage3_episode_recorder.py`
- `tests/test_stage3_runtime_demo_cli.py`

Modify:

- `README.md`: add Stage 3 runtime demo command after implementation.
- `README.zh-CN.md`: add matching Chinese doc/demo link after implementation.
- `docs/project_current_status.md`: update current verification count and Stage 3 MVP status after implementation.

Do not modify:

- Existing `gateway/` behavior.
- Existing benchmark/scorer/report contracts.
- Existing PyBullet backend semantics.
- Existing `robots/base.py` or `robots/mock_realman_6dof.py` unless a test proves a real integration issue.

---

### Task 1: Runtime Types

**Files:**
- Create: `robot_runtime/__init__.py`
- Create: `robot_runtime/types.py`
- Test: `tests/test_stage3_runtime_types.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_stage3_runtime_types.py`:

```python
from robot_runtime.types import RobotAction, RobotObservation


def test_robot_observation_serializes_to_dict():
    observation = RobotObservation(
        robot_id="mock_realman_6dof",
        joint_positions=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5),
        timestamp="2026-06-11T10:00:00Z",
        metadata={"source": "test"},
    )

    assert observation.to_dict() == {
        "robot_id": "mock_realman_6dof",
        "joint_positions": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
        "timestamp": "2026-06-11T10:00:00Z",
        "metadata": {"source": "test"},
    }


def test_robot_action_serializes_to_dict():
    action = RobotAction(
        action_type="joint_move",
        target_joints=(0.1, 0.2, 0.0, 0.0, 0.0, 0.0),
        speed=0.2,
        source="replay",
        metadata={"command_id": "cmd_simple_joint_move_001"},
    )

    assert action.to_dict() == {
        "action_type": "joint_move",
        "target_joints": [0.1, 0.2, 0.0, 0.0, 0.0, 0.0],
        "speed": 0.2,
        "source": "replay",
        "metadata": {"command_id": "cmd_simple_joint_move_001"},
    }


def test_robot_action_rejects_non_joint_move():
    try:
        RobotAction(action_type="cartesian_move", target_joints=(0.0,) * 6)
    except ValueError as exc:
        assert "only supports joint_move" in str(exc)
    else:
        raise AssertionError("RobotAction should reject unsupported action_type")
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_runtime_types.py -q --basetemp .pytest_tmp\stage3_types_red
```

Expected: collection/import fails because `robot_runtime.types` does not exist.

- [ ] **Step 3: Implement runtime types**

Create `robot_runtime/types.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from robot_safety.models import SafetyResult


def _float_tuple(values, field_name: str) -> tuple[float, ...]:
    try:
        result = tuple(float(item) for item in values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of numbers") from exc
    if len(result) != 6:
        raise ValueError(f"{field_name} must contain six values")
    return result


@dataclass(frozen=True)
class RobotObservation:
    robot_id: str
    joint_positions: tuple[float, ...]
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "joint_positions", _float_tuple(self.joint_positions, "joint_positions"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "robot_id": self.robot_id,
            "joint_positions": list(self.joint_positions),
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RobotAction:
    action_type: str
    target_joints: tuple[float, ...]
    speed: float = 0.1
    source: str = "replay"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.action_type != "joint_move":
            raise ValueError("Stage 3 MVP only supports joint_move actions")
        if self.speed <= 0.0:
            raise ValueError("speed must be positive")
        object.__setattr__(self, "target_joints", _float_tuple(self.target_joints, "target_joints"))
        object.__setattr__(self, "speed", float(self.speed))

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "target_joints": list(self.target_joints),
            "speed": self.speed,
            "source": self.source,
            "metadata": dict(self.metadata),
        }


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

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "observation": self.observation.to_dict(),
            "proposed_action": self.proposed_action.to_dict(),
            "safety_result": self.safety_result.to_dict(),
            "backend_metadata": dict(self.backend_metadata),
            "executed": self.executed,
            "sent_action": self.sent_action.to_dict() if self.sent_action else None,
            "blocked_reason": self.blocked_reason,
            "episode_step_path": str(self.episode_step_path) if self.episode_step_path else None,
        }
```

Create `robot_runtime/__init__.py`:

```python
"""LeRobot-compatible safety runtime primitives."""

from .types import RobotAction, RobotObservation, RuntimeStepResult

__all__ = ["RobotAction", "RobotObservation", "RuntimeStepResult"]
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_runtime_types.py -q --basetemp .pytest_tmp\stage3_types_green
```

Expected: `3 passed`.

---

### Task 2: Device Protocol And MockRealManDevice

**Files:**
- Create: `robot_runtime/device.py`
- Create: `robot_runtime/adapters/__init__.py`
- Create: `robot_runtime/adapters/mock_realman_device.py`
- Test: `tests/test_stage3_mock_realman_device.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_stage3_mock_realman_device.py`:

```python
import pytest

from robot_runtime.adapters.mock_realman_device import MockRealManDevice
from robot_runtime.types import RobotAction


def test_mock_realman_device_connect_enables_observation():
    device = MockRealManDevice(initial_joints=(0.0,) * 6)

    assert device.is_connected is False
    device.connect()
    observation = device.get_observation()

    assert device.is_connected is True
    assert observation.robot_id == "mock_realman_6dof"
    assert observation.joint_positions == (0.0,) * 6
    assert "timestamp" in observation.to_dict()


def test_mock_realman_device_send_action_requires_connection():
    device = MockRealManDevice(initial_joints=(0.0,) * 6)
    action = RobotAction(action_type="joint_move", target_joints=(0.1,) * 6)

    with pytest.raises(ConnectionError, match="not connected"):
        device.send_action(action)


def test_mock_realman_device_send_action_updates_joint_state():
    device = MockRealManDevice(initial_joints=(0.0,) * 6)
    device.connect()
    action = RobotAction(action_type="joint_move", target_joints=(0.1, 0.2, 0.0, 0.0, 0.0, 0.0), speed=0.2)

    sent = device.send_action(action)

    assert sent == action
    assert device.get_observation().joint_positions == action.target_joints
    assert device.execution_count == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_mock_realman_device.py -q --basetemp .pytest_tmp\stage3_device_red
```

Expected: collection/import fails because `robot_runtime.adapters.mock_realman_device` does not exist.

- [ ] **Step 3: Implement protocol and mock device**

Create `robot_runtime/device.py`:

```python
from __future__ import annotations

from typing import Protocol

from .types import RobotAction, RobotObservation


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

Create `robot_runtime/adapters/__init__.py`:

```python
"""Runtime robot device adapters."""

from .mock_realman_device import MockRealManDevice

__all__ = ["MockRealManDevice"]
```

Create `robot_runtime/adapters/mock_realman_device.py`:

```python
from __future__ import annotations

from datetime import datetime, timezone

from robots.mock_realman_6dof import MockRealMan6DoFAdapter

from ..types import RobotAction, RobotObservation


class MockRealManDevice:
    name = "mock_realman_device"

    def __init__(
        self,
        *,
        robot_id: str = "mock_realman_6dof",
        initial_joints: tuple[float, ...] | list[float] | None = None,
    ) -> None:
        self._adapter = MockRealMan6DoFAdapter(robot_id=robot_id, initial_joints=initial_joints)
        self._connected = False

    @property
    def observation_features(self) -> dict:
        return {"joint_positions": (6,)}

    @property
    def action_features(self) -> dict:
        return {"target_joints": (6,), "speed": float}

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def robot_id(self) -> str:
        return self._adapter.robot_id

    @property
    def execution_count(self) -> int:
        return self._adapter.execution_count

    def connect(self, calibrate: bool = True) -> None:
        self._connected = True

    def get_observation(self) -> RobotObservation:
        self._require_connected()
        return RobotObservation(
            robot_id=self.robot_id,
            joint_positions=self._adapter.get_joint_state(),
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata={"device": self.name},
        )

    def send_action(self, action: RobotAction) -> RobotAction:
        self._require_connected()
        self._adapter.execute_joint_move(action.target_joints, action.speed)
        return action

    def disconnect(self) -> None:
        self._connected = False

    def _require_connected(self) -> None:
        if not self._connected:
            raise ConnectionError(f"{self.name} is not connected")
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_mock_realman_device.py -q --basetemp .pytest_tmp\stage3_device_green
```

Expected: `3 passed`.

---

### Task 3: ReplayActionSource And StaticSceneProvider

**Files:**
- Create: `robot_runtime/action_source.py`
- Create: `robot_runtime/scene_provider.py`
- Test: `tests/test_stage3_replay_action_source.py`
- Test: `tests/test_stage3_scene_provider.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_stage3_replay_action_source.py`:

```python
from pathlib import Path

from robot_runtime.action_source import ReplayActionSource


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_replay_action_source_reads_command_json():
    task_dir = BENCH / "simple_joint_move_001"
    source = ReplayActionSource(task_dir / "command.json")
    observation = object()

    action = source.propose_action(observation)

    assert source.name == "replay"
    assert action.action_type == "joint_move"
    assert action.source == "replay"
    assert action.metadata["command_id"] == "cmd_simple_joint_move_001"
    assert len(action.target_joints) == 6
```

Create `tests/test_stage3_scene_provider.py`:

```python
from pathlib import Path

from robot_runtime.scene_provider import StaticSceneProvider
from robot_runtime.types import RobotObservation


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_static_scene_provider_reads_scene_json():
    task_dir = BENCH / "simple_joint_move_001"
    provider = StaticSceneProvider(task_dir / "scene.json")
    observation = RobotObservation(
        robot_id="mock_realman_6dof",
        joint_positions=(0.0,) * 6,
        timestamp="2026-06-11T10:00:00Z",
    )

    scene = provider.get_scene(observation)

    assert provider.name == "static_scene"
    assert scene.scene_id == "simple_joint_move_001"
    assert len(scene.robot.joint_names) == 6
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_replay_action_source.py tests\test_stage3_scene_provider.py -q --basetemp .pytest_tmp\stage3_sources_red
```

Expected: collection/import fails because `robot_runtime.action_source` and `robot_runtime.scene_provider` do not exist.

- [ ] **Step 3: Implement action source and scene provider**

Create `robot_runtime/action_source.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from robot_safety.models import JointCommand

from .types import RobotAction, RobotObservation


class ActionSource(Protocol):
    name: str

    def propose_action(self, observation: RobotObservation) -> RobotAction:
        ...


class ReplayActionSource:
    name = "replay"

    def __init__(self, command_path: str | Path) -> None:
        self.command_path = Path(command_path)
        self.command = JointCommand.from_json(self.command_path)

    def propose_action(self, observation: RobotObservation) -> RobotAction:
        return RobotAction(
            action_type=self.command.command_type,
            target_joints=self.command.target_joints,
            speed=self.command.speed,
            source="replay",
            metadata={
                "command_id": self.command.command_id,
                "command_path": str(self.command_path),
                "original_source": self.command.source,
            },
        )
```

Create `robot_runtime/scene_provider.py`:

```python
from __future__ import annotations

from pathlib import Path
from typing import Protocol

from robot_safety.models import Scene

from .types import RobotObservation


class SceneProvider(Protocol):
    name: str

    def get_scene(self, observation: RobotObservation) -> Scene:
        ...


class StaticSceneProvider:
    name = "static_scene"

    def __init__(self, scene_path: str | Path) -> None:
        self.scene_path = Path(scene_path)
        self.scene = Scene.from_json(self.scene_path)

    def get_scene(self, observation: RobotObservation) -> Scene:
        return self.scene
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_replay_action_source.py tests\test_stage3_scene_provider.py -q --basetemp .pytest_tmp\stage3_sources_green
```

Expected: `2 passed`.

---

### Task 4: EpisodeRecorder

**Files:**
- Create: `robot_runtime/episode_recorder.py`
- Test: `tests/test_stage3_episode_recorder.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_stage3_episode_recorder.py`:

```python
import json
from pathlib import Path

from robot_runtime.episode_recorder import EpisodeRecorder
from robot_runtime.types import RobotAction, RobotObservation, RuntimeStepResult
from robot_safety.models import SafetyResult


def _safe_result():
    return SafetyResult(
        scene_id="scene",
        command_id="cmd",
        decision="approve",
        risk_level="low",
        joint_limits_ok=True,
        trajectory_collision_free=True,
        self_collision_checked=False,
        self_collision_free=None,
        min_clearance=0.2,
        closest_robot_link="link_1",
        closest_obstacle="sphere",
        worst_step=0,
        max_joint_delta=0.1,
        violations=(),
        evidence=("safe",),
    )


def test_episode_recorder_writes_metadata_and_steps_jsonl(tmp_path):
    recorder = EpisodeRecorder(
        root_dir=tmp_path,
        robot_name="mock_realman_device",
        action_source_name="replay",
        scene_provider_name="static_scene",
        backend_name="mock",
    )
    result = RuntimeStepResult(
        step_id="step_000001",
        observation=RobotObservation("mock_realman_6dof", (0.0,) * 6, "2026-06-11T10:00:00Z"),
        proposed_action=RobotAction("joint_move", (0.1,) * 6),
        safety_result=_safe_result(),
        backend_metadata={"name": "mock"},
        executed=True,
        sent_action=RobotAction("joint_move", (0.1,) * 6),
        blocked_reason=None,
    )

    step_path = recorder.record_step(result)

    metadata = json.loads((recorder.episode_dir / "metadata.json").read_text(encoding="utf-8"))
    lines = (recorder.episode_dir / "steps.jsonl").read_text(encoding="utf-8").splitlines()
    step = json.loads(lines[0])

    assert metadata["schema_version"] == "stage3.runtime_episode.v1"
    assert metadata["robot"] == "mock_realman_device"
    assert step_path == recorder.episode_dir / "steps.jsonl"
    assert step["step_id"] == "step_000001"
    assert step["executed"] is True
    assert step["safety_result"]["decision"] == "approve"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_episode_recorder.py -q --basetemp .pytest_tmp\stage3_recorder_red
```

Expected: collection/import fails because `robot_runtime.episode_recorder` does not exist.

- [ ] **Step 3: Implement EpisodeRecorder**

Create `robot_runtime/episode_recorder.py`:

```python
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .types import RuntimeStepResult


class EpisodeRecorder:
    schema_version = "stage3.runtime_episode.v1"

    def __init__(
        self,
        *,
        root_dir: str | Path,
        robot_name: str,
        action_source_name: str,
        scene_provider_name: str,
        backend_name: str,
        episode_id: str | None = None,
    ) -> None:
        self.root_dir = Path(root_dir)
        self.episode_id = episode_id or self._make_episode_id()
        self.episode_dir = self.root_dir / self.episode_id
        self.episode_dir.mkdir(parents=True, exist_ok=True)
        self.steps_path = self.episode_dir / "steps.jsonl"
        self.metadata_path = self.episode_dir / "metadata.json"
        self._write_metadata(
            robot_name=robot_name,
            action_source_name=action_source_name,
            scene_provider_name=scene_provider_name,
            backend_name=backend_name,
        )

    def record_step(self, result: RuntimeStepResult) -> Path:
        with self.steps_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(result.to_dict(), indent=None) + "\n")
        return self.steps_path

    def _write_metadata(
        self,
        *,
        robot_name: str,
        action_source_name: str,
        scene_provider_name: str,
        backend_name: str,
    ) -> None:
        payload = {
            "schema_version": self.schema_version,
            "episode_id": self.episode_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "robot": robot_name,
            "action_source": action_source_name,
            "scene_provider": scene_provider_name,
            "backend": backend_name,
        }
        self.metadata_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @staticmethod
    def _make_episode_id() -> str:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"episode_{stamp}_{uuid4().hex[:8]}"
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_episode_recorder.py -q --basetemp .pytest_tmp\stage3_recorder_green
```

Expected: `1 passed`.

---

### Task 5: SafetyRuntime

**Files:**
- Create: `robot_runtime/safety_runtime.py`
- Test: `tests/test_stage3_safety_runtime.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_stage3_safety_runtime.py`:

```python
from pathlib import Path

from robot_runtime.action_source import ReplayActionSource
from robot_runtime.adapters.mock_realman_device import MockRealManDevice
from robot_runtime.episode_recorder import EpisodeRecorder
from robot_runtime.safety_runtime import SafetyRuntime, action_to_joint_command
from robot_runtime.scene_provider import StaticSceneProvider
from robot_runtime.types import RobotAction, RobotObservation
from sim.backend_factory import create_backend


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_action_to_joint_command_uses_observation_and_action():
    observation = RobotObservation("mock_realman_6dof", (0.0,) * 6, "2026-06-11T10:00:00Z")
    action = RobotAction("joint_move", (0.1,) * 6, speed=0.2, source="replay")

    command = action_to_joint_command(observation, action, step_id="step_000001")

    assert command.command_id == "runtime_step_000001"
    assert command.current_joints == (0.0,) * 6
    assert command.target_joints == (0.1,) * 6
    assert command.speed == 0.2
    assert command.source == "replay"


def _runtime_for_task(task_name: str, tmp_path):
    task_dir = BENCH / task_name
    robot = MockRealManDevice(initial_joints=(0.0,) * 6)
    robot.connect()
    action_source = ReplayActionSource(task_dir / "command.json")
    scene_provider = StaticSceneProvider(task_dir / "scene.json")
    recorder = EpisodeRecorder(
        root_dir=tmp_path,
        robot_name=robot.name,
        action_source_name=action_source.name,
        scene_provider_name=scene_provider.name,
        backend_name="mock",
    )
    return SafetyRuntime(
        robot=robot,
        action_source=action_source,
        scene_provider=scene_provider,
        backend=create_backend("mock"),
        recorder=recorder,
    ), robot


def test_safety_runtime_executes_approved_action(tmp_path):
    runtime, robot = _runtime_for_task("simple_joint_move_001", tmp_path)

    result = runtime.step()

    assert result.safety_result.decision == "approve"
    assert result.executed is True
    assert result.sent_action is not None
    assert robot.execution_count == 1


def test_safety_runtime_blocks_rejected_action(tmp_path):
    runtime, robot = _runtime_for_task("obstacle_collision_001", tmp_path)

    result = runtime.step()

    assert result.safety_result.decision == "reject"
    assert result.executed is False
    assert result.sent_action is None
    assert result.blocked_reason == "rejected_by_safety_gate"
    assert robot.execution_count == 0


def test_safety_runtime_blocks_manual_review_action(tmp_path):
    runtime, robot = _runtime_for_task("near_miss_clearance_001", tmp_path)

    result = runtime.step()

    assert result.safety_result.decision == "manual_review"
    assert result.executed is False
    assert result.sent_action is None
    assert result.blocked_reason == "manual_review_required"
    assert robot.execution_count == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_safety_runtime.py -q --basetemp .pytest_tmp\stage3_runtime_red
```

Expected: collection/import fails because `robot_runtime.safety_runtime` does not exist.

- [ ] **Step 3: Implement SafetyRuntime**

Create `robot_runtime/safety_runtime.py`:

```python
from __future__ import annotations

from robot_safety.evaluator import evaluate_joint_command_with_metadata
from robot_safety.models import JointCommand

from .action_source import ActionSource
from .device import RobotDeviceAdapter
from .episode_recorder import EpisodeRecorder
from .scene_provider import SceneProvider
from .types import RobotAction, RobotObservation, RuntimeStepResult


def action_to_joint_command(observation: RobotObservation, action: RobotAction, *, step_id: str) -> JointCommand:
    return JointCommand(
        command_id=f"runtime_{step_id}",
        command_type=action.action_type,
        current_joints=observation.joint_positions,
        target_joints=action.target_joints,
        speed=action.speed,
        source=action.source,
    )


class SafetyRuntime:
    def __init__(
        self,
        *,
        robot: RobotDeviceAdapter,
        action_source: ActionSource,
        scene_provider: SceneProvider,
        backend,
        recorder: EpisodeRecorder | None = None,
    ) -> None:
        self.robot = robot
        self.action_source = action_source
        self.scene_provider = scene_provider
        self.backend = backend
        self.recorder = recorder
        self._step_index = 0

    def step(self) -> RuntimeStepResult:
        self._step_index += 1
        step_id = f"step_{self._step_index:06d}"
        observation = self.robot.get_observation()
        action = self.action_source.propose_action(observation)
        scene = self.scene_provider.get_scene(observation)
        command = action_to_joint_command(observation, action, step_id=step_id)
        outcome = evaluate_joint_command_with_metadata(scene, command, backend=self.backend)

        sent_action = None
        executed = False
        blocked_reason = _blocked_reason(outcome.safety_result.decision)
        if outcome.safety_result.decision == "approve":
            sent_action = self.robot.send_action(action)
            executed = True
            blocked_reason = None

        result = RuntimeStepResult(
            step_id=step_id,
            observation=observation,
            proposed_action=action,
            safety_result=outcome.safety_result,
            backend_metadata=outcome.backend_metadata,
            executed=executed,
            sent_action=sent_action,
            blocked_reason=blocked_reason,
        )
        if self.recorder is not None:
            path = self.recorder.record_step(result)
            result = RuntimeStepResult(
                step_id=result.step_id,
                observation=result.observation,
                proposed_action=result.proposed_action,
                safety_result=result.safety_result,
                backend_metadata=result.backend_metadata,
                executed=result.executed,
                sent_action=result.sent_action,
                blocked_reason=result.blocked_reason,
                episode_step_path=path,
            )
        return result


def _blocked_reason(decision: str) -> str:
    if decision == "manual_review":
        return "manual_review_required"
    if decision == "reject":
        return "rejected_by_safety_gate"
    return "approved_by_safety_gate"
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_safety_runtime.py -q --basetemp .pytest_tmp\stage3_runtime_green
```

Expected: `4 passed`.

---

### Task 6: Runtime Demo CLI

**Files:**
- Create: `cli/run_runtime_demo.py`
- Test: `tests/test_stage3_runtime_demo_cli.py`
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/project_current_status.md`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_stage3_runtime_demo_cli.py`:

```python
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def _run_demo(task_name: str, tmp_path):
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.run_runtime_demo",
            "--task",
            str(BENCH / task_name),
            "--backend",
            "mock",
            "--episode-dir",
            str(tmp_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def test_runtime_demo_cli_executes_safe_task(tmp_path):
    payload = _run_demo("simple_joint_move_001", tmp_path)

    assert payload["safety_result"]["decision"] == "approve"
    assert payload["executed"] is True
    assert Path(payload["episode_step_path"]).exists()


def test_runtime_demo_cli_blocks_rejected_task(tmp_path):
    payload = _run_demo("obstacle_collision_001", tmp_path)

    assert payload["safety_result"]["decision"] == "reject"
    assert payload["executed"] is False
    assert payload["blocked_reason"] == "rejected_by_safety_gate"


def test_runtime_demo_cli_blocks_manual_review_task(tmp_path):
    payload = _run_demo("near_miss_clearance_001", tmp_path)

    assert payload["safety_result"]["decision"] == "manual_review"
    assert payload["executed"] is False
    assert payload["blocked_reason"] == "manual_review_required"
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_runtime_demo_cli.py -q --basetemp .pytest_tmp\stage3_cli_red
```

Expected: subprocess fails with `No module named cli.run_runtime_demo`.

- [ ] **Step 3: Implement CLI**

Create `cli/run_runtime_demo.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from robot_runtime.action_source import ReplayActionSource
from robot_runtime.adapters.mock_realman_device import MockRealManDevice
from robot_runtime.episode_recorder import EpisodeRecorder
from robot_runtime.safety_runtime import SafetyRuntime
from robot_runtime.scene_provider import StaticSceneProvider
from sim.backend_factory import create_backend


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Stage 3 runtime MVP demo task.")
    parser.add_argument("--task", required=True, help="Benchmark task directory containing scene.json and command.json")
    parser.add_argument("--backend", default="mock", choices=("mock", "pybullet"))
    parser.add_argument("--episode-dir", default="output_reports/runtime_demo")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    task_dir = Path(args.task)
    scene_path = task_dir / "scene.json"
    command_path = task_dir / "command.json"
    action_source = ReplayActionSource(command_path)
    scene_provider = StaticSceneProvider(scene_path)
    initial_joints = action_source.command.current_joints
    robot = MockRealManDevice(initial_joints=initial_joints)
    robot.connect()
    backend = create_backend(args.backend)
    recorder = EpisodeRecorder(
        root_dir=args.episode_dir,
        robot_name=robot.name,
        action_source_name=action_source.name,
        scene_provider_name=scene_provider.name,
        backend_name=args.backend,
    )
    runtime = SafetyRuntime(
        robot=robot,
        action_source=action_source,
        scene_provider=scene_provider,
        backend=backend,
        recorder=recorder,
    )
    result = runtime.step()
    payload = result.to_dict()
    if args.json:
        print(json.dumps(payload, indent=2))
        return
    print(f"Decision: {result.safety_result.decision}")
    print(f"Risk Level: {result.safety_result.risk_level}")
    print(f"Executed: {result.executed}")
    print(f"Blocked Reason: {result.blocked_reason}")
    print(f"Episode Step Path: {result.episode_step_path}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run CLI tests to verify they pass**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_runtime_demo_cli.py -q --basetemp .pytest_tmp\stage3_cli_green
```

Expected: `3 passed`.

- [ ] **Step 5: Update docs after CLI works**

Add a short command block to `README.md` under Quick Start:

```markdown
Run the Stage 3 runtime MVP demo:

```bash
python -m cli.run_runtime_demo ^
  --task bench\sim_robot_arm\simple_joint_move_001 ^
  --backend mock ^
  --episode-dir output_reports\runtime_demo ^
  --json
```
```

Add the equivalent Chinese note to `README.zh-CN.md`.

Update `docs/project_current_status.md` completed scope with:

```markdown
- Stage 3 MVP: LeRobot-compatible safety runtime design and minimal runtime demo.
```

---

### Task 7: Full Verification And Demo Runs

**Files:**
- No new files.

- [ ] **Step 1: Run all focused Stage 3 tests**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest tests\test_stage3_runtime_types.py tests\test_stage3_mock_realman_device.py tests\test_stage3_replay_action_source.py tests\test_stage3_scene_provider.py tests\test_stage3_episode_recorder.py tests\test_stage3_safety_runtime.py tests\test_stage3_runtime_demo_cli.py -q --basetemp .pytest_tmp\stage3_all
```

Expected: all Stage 3 tests pass.

- [ ] **Step 2: Run full test suite**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp\stage3_full
```

Expected: all existing tests plus new Stage 3 tests pass.

- [ ] **Step 3: Run safe runtime demo**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.run_runtime_demo --task bench\sim_robot_arm\simple_joint_move_001 --backend mock --episode-dir output_reports\runtime_demo_safe --json
```

Expected JSON:

```json
{
  "safety_result": {
    "decision": "approve"
  },
  "executed": true,
  "blocked_reason": null
}
```

- [ ] **Step 4: Run manual-review runtime demo**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.run_runtime_demo --task bench\sim_robot_arm\near_miss_clearance_001 --backend mock --episode-dir output_reports\runtime_demo_manual_review --json
```

Expected JSON:

```json
{
  "safety_result": {
    "decision": "manual_review"
  },
  "executed": false,
  "blocked_reason": "manual_review_required"
}
```

- [ ] **Step 5: Run rejected runtime demo**

Run:

```powershell
D:\miniforge3\envs\robotarm-pybullet\python.exe -m cli.run_runtime_demo --task bench\sim_robot_arm\obstacle_collision_001 --backend mock --episode-dir output_reports\runtime_demo_reject --json
```

Expected JSON:

```json
{
  "safety_result": {
    "decision": "reject"
  },
  "executed": false,
  "blocked_reason": "rejected_by_safety_gate"
}
```

- [ ] **Step 6: Inspect episode outputs**

Check that these files exist:

```text
output_reports/runtime_demo_safe/<episode_id>/metadata.json
output_reports/runtime_demo_safe/<episode_id>/steps.jsonl
output_reports/runtime_demo_manual_review/<episode_id>/metadata.json
output_reports/runtime_demo_manual_review/<episode_id>/steps.jsonl
output_reports/runtime_demo_reject/<episode_id>/metadata.json
output_reports/runtime_demo_reject/<episode_id>/steps.jsonl
```

Expected: each `steps.jsonl` has one line and the `executed` flag matches the task decision.

---

## Self-Review Checklist

- [ ] Every component in `docs/stage3_runtime_mvp_design.md` maps to a task above.
- [ ] `SceneProvider` is included explicitly.
- [ ] Safe, manual-review, and rejected paths are all tested.
- [ ] No task depends on real RealMan SDK, LeRobot, LLM, vision, teleoperation, or planning.
- [ ] Existing `gateway/`, `benchmark/`, `scorer/`, and `reports/` behavior remains unchanged.
- [ ] Full pytest passes after implementation.

## Commit Checkpoints

Use these only after the relevant tests pass:

```powershell
git add robot_runtime\__init__.py robot_runtime\types.py tests\test_stage3_runtime_types.py
git commit -m "feat: add stage 3 runtime types"

git add robot_runtime\device.py robot_runtime\adapters\__init__.py robot_runtime\adapters\mock_realman_device.py tests\test_stage3_mock_realman_device.py
git commit -m "feat: add mock runtime robot device"

git add robot_runtime\action_source.py robot_runtime\scene_provider.py tests\test_stage3_replay_action_source.py tests\test_stage3_scene_provider.py
git commit -m "feat: add runtime action and scene sources"

git add robot_runtime\episode_recorder.py tests\test_stage3_episode_recorder.py
git commit -m "feat: add runtime episode recorder"

git add robot_runtime\safety_runtime.py tests\test_stage3_safety_runtime.py
git commit -m "feat: add stage 3 safety runtime"

git add cli\run_runtime_demo.py tests\test_stage3_runtime_demo_cli.py README.md README.zh-CN.md docs\project_current_status.md
git commit -m "feat: add runtime demo CLI"
```
