# Stage 2.3 PyBullet Backend Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a minimal PyBullet backend that loads the project URDF and runs through the existing safety review pipeline.

**Architecture:** Keep `SimulationBackend` as the stable boundary. Add `PyBulletBackend` beside `MockGeometryBackend`, register it in `sim/backend_factory.py`, and expose it through the existing gateway and CLI `--backend` argument. The first version uses PyBullet DIRECT mode, resets joint states along the interpolated trajectory, samples link positions, and computes sphere-obstacle clearance in the same result shape as the mock backend.

**Tech Stack:** Python 3.10, PyBullet, pytest, existing `robot_safety` models and `sim` backend abstractions.

---

### Task 1: Register Backend Factory Behavior

**Files:**
- Modify: `sim/backend_factory.py`
- Test: `tests/test_stage2_pybullet_backend_factory.py`

**Step 1: Write the failing tests**

Create `tests/test_stage2_pybullet_backend_factory.py`:

```python
import pytest

from sim.backend_factory import create_backend


def test_create_pybullet_backend_when_pybullet_available():
    pytest.importorskip("pybullet")

    backend = create_backend("pybullet")

    assert backend.name == "pybullet"


def test_create_pybullet_backend_reports_missing_dependency(monkeypatch):
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pybullet":
            raise ImportError("simulated missing pybullet")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="pybullet"):
        create_backend("pybullet")
```

**Step 2: Run test to verify it fails**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m pytest tests/test_stage2_pybullet_backend_factory.py -q
```

Expected: FAIL because `pybullet` is not registered.

**Step 3: Implement minimal factory support**

Modify `sim/backend_factory.py`:

```python
from .mock_backend import MockGeometryBackend


def create_backend(name: str):
    normalized = name.lower().strip()
    if normalized == "mock":
        return MockGeometryBackend()
    if normalized == "pybullet":
        try:
            import pybullet  # noqa: F401
            from .pybullet_backend import PyBulletBackend
        except ImportError as exc:
            raise RuntimeError(
                "PyBullet backend requires optional dependency 'pybullet'. "
                "Install it with: pip install -r requirements-sim.txt "
                "or conda install -c conda-forge pybullet."
            ) from exc
        return PyBulletBackend()
    raise ValueError(f"unsupported simulation backend: {name}")
```

**Step 4: Run test to verify it passes**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m pytest tests/test_stage2_pybullet_backend_factory.py -q
```

Expected: PASS after `sim/pybullet_backend.py` exists in Task 2.

---

### Task 2: Add Minimal PyBullet Backend Skeleton

**Files:**
- Create: `sim/pybullet_backend.py`
- Test: `tests/test_stage2_pybullet_backend.py`

**Step 1: Write failing backend smoke tests**

Create `tests/test_stage2_pybullet_backend.py`:

```python
from pathlib import Path

import pytest

from robot_safety.models import JointCommand, Scene
from robot_safety.trajectory import interpolate_joint_trajectory
from sim.pybullet_backend import PyBulletBackend


ROOT = Path(__file__).resolve().parents[1]


def test_pybullet_backend_loads_default_urdf():
    pytest.importorskip("pybullet")

    backend = PyBulletBackend()

    assert backend.name == "pybullet"
    assert backend.urdf_path.exists()


def test_pybullet_backend_returns_review_result_for_simple_scene():
    pytest.importorskip("pybullet")

    task_dir = ROOT / "bench" / "sim_robot_arm" / "simple_joint_move_001"
    scene = Scene.from_json(task_dir / "scene.json")
    command = JointCommand.from_json(task_dir / "command.json")
    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )

    result = PyBulletBackend().replay_joint_trajectory(scene=scene, trajectory=trajectory)

    assert result.backend_name == "pybullet"
    assert result.collision_free is True
    assert result.min_clearance == 999.0
    assert result.closest_robot_link is None
    assert result.closest_obstacle is None
    assert result.violations == ()
    assert result.metadata["mode"] == "DIRECT"
```

**Step 2: Run test to verify it fails**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m pytest tests/test_stage2_pybullet_backend.py -q
```

Expected: FAIL because `sim.pybullet_backend` does not exist.

**Step 3: Implement backend skeleton**

Create `sim/pybullet_backend.py`:

```python
"""PyBullet backend for replaying joint trajectories against a URDF arm."""

from __future__ import annotations

from pathlib import Path

from .base import BackendReviewResult, SimulationBackend


class PyBulletBackend(SimulationBackend):
    name = "pybullet"

    def __init__(self, urdf_path: Path | None = None) -> None:
        self.urdf_path = urdf_path or (
            Path(__file__).resolve().parents[1]
            / "assets"
            / "robots"
            / "mock_realman_6dof"
            / "robot.urdf"
        )

    def replay_joint_trajectory(self, *, scene, trajectory) -> BackendReviewResult:
        import pybullet

        client_id = pybullet.connect(pybullet.DIRECT)
        try:
            robot_id = pybullet.loadURDF(str(self.urdf_path), physicsClientId=client_id)
            if robot_id < 0:
                raise RuntimeError(f"failed to load URDF: {self.urdf_path}")
            return BackendReviewResult(
                backend_name=self.name,
                collision_free=True,
                min_clearance=999.0,
                closest_robot_link=None,
                closest_obstacle=None,
                worst_step=None,
                violations=(),
                metadata={
                    "mode": "DIRECT",
                    "urdf_path": str(self.urdf_path),
                    "collision_method": "link_position_sphere_clearance",
                },
            )
        finally:
            pybullet.disconnect(client_id)
```

**Step 4: Run tests**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m pytest tests/test_stage2_pybullet_backend.py tests/test_stage2_pybullet_backend_factory.py -q
```

Expected: PASS.

---

### Task 3: Implement Sphere Clearance Replay

**Files:**
- Modify: `sim/pybullet_backend.py`
- Test: `tests/test_stage2_pybullet_backend.py`

**Step 1: Add failing collision/clearance test**

Append to `tests/test_stage2_pybullet_backend.py`:

```python
def test_pybullet_backend_detects_sphere_collision_near_base_link():
    pytest.importorskip("pybullet")

    scene = Scene.from_dict(
        {
            "scene_id": "pybullet_base_collision_001",
            "robot": {
                "robot_id": "mock_realman_6dof",
                "model_type": "mock_6dof",
                "joint_names": ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"],
                "link_radius": 0.025,
                "link_lengths": [0.18, 0.32, 0.28, 0.2, 0.14, 0.1],
                "joint_limits": [
                    [-3.14, 3.14],
                    [-1.57, 1.57],
                    [-2.2, 2.2],
                    [-3.14, 3.14],
                    [-1.8, 1.8],
                    [-3.14, 3.14],
                ],
            },
            "obstacles": [
                {
                    "obstacle_id": "base_overlap",
                    "type": "sphere",
                    "position": [0.0, 0.0, 0.15],
                    "radius": 0.2,
                }
            ],
            "safety_config": {"min_clearance": 0.05},
        }
    )
    command = JointCommand.from_dict(
        {
            "command_id": "hold_position_001",
            "command_type": "joint_move",
            "current_joints": [0, 0, 0, 0, 0, 0],
            "target_joints": [0, 0, 0, 0, 0, 0],
            "speed": 0.2,
        }
    )
    trajectory = interpolate_joint_trajectory(
        command.current_joints,
        command.target_joints,
        scene.safety_config.num_interpolation_steps,
    )

    result = PyBulletBackend().replay_joint_trajectory(scene=scene, trajectory=trajectory)

    assert result.collision_free is False
    assert result.min_clearance < 0
    assert result.closest_obstacle == "base_overlap"
    assert result.closest_robot_link is not None
    assert result.worst_step == 0
    assert result.violations
```

**Step 2: Run test to verify it fails**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m pytest tests/test_stage2_pybullet_backend.py -q
```

Expected: FAIL because `collision_free` is always true.

**Step 3: Implement minimal link-position clearance**

Update `PyBulletBackend.replay_joint_trajectory`:

- Load URDF.
- Discover revolute joint indices.
- For each trajectory step, call `pybullet.resetJointState`.
- For each link, call `pybullet.getLinkState`.
- Compare link position to each sphere obstacle center.
- Approximate link radius as `0.05`.
- Track minimum clearance, closest link, closest obstacle, worst step, and collision.

Keep obstacle support limited to `type == "sphere"` for this task.

**Step 4: Run focused tests**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m pytest tests/test_stage2_pybullet_backend.py -q
```

Expected: PASS.

---

### Task 4: Wire CLI Choices

**Files:**
- Modify: `cli/review_command.py`
- Modify: `cli/execute_if_safe.py`
- Modify: `cli/run_benchmark.py`
- Test: `tests/test_stage2_backend_cli.py`

**Step 1: Add failing CLI test**

Append to `tests/test_stage2_backend_cli.py`:

```python
def test_review_command_cli_accepts_pybullet_backend(tmp_path):
    pytest.importorskip("pybullet")

    scene = ROOT / "bench" / "sim_robot_arm" / "simple_joint_move_001" / "scene.json"
    command = ROOT / "bench" / "sim_robot_arm" / "simple_joint_move_001" / "command.json"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.review_command",
            "--scene",
            str(scene),
            "--command",
            str(command),
            "--backend",
            "pybullet",
            "--log-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert "Decision:" in result.stdout
```

**Step 2: Run test to verify it fails**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m pytest tests/test_stage2_backend_cli.py::test_review_command_cli_accepts_pybullet_backend -q
```

Expected: FAIL because CLI choices only allow `mock`.

**Step 3: Update CLI choices**

In `cli/review_command.py`, `cli/execute_if_safe.py`, and `cli/run_benchmark.py`, change backend choices:

```python
choices=["mock", "pybullet"]
```

**Step 4: Run CLI tests**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m pytest tests/test_stage2_backend_cli.py -q
```

Expected: PASS.

---

### Task 5: Verify Full Project and Benchmark

**Files:**
- Modify: `README.md` only if commands or backend behavior changed

**Step 1: Run full test suite**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m pytest -q
```

Expected: PASS.

**Step 2: Run mock benchmark**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m cli.run_benchmark --backend mock --bench bench\sim_robot_arm --log-dir logs\benchmark --output-json output_reports\stage1_benchmark_summary.json --output-md output_reports\stage1_benchmark_summary.md
```

Expected: `8 / 8 passed`.

**Step 3: Run PyBullet backend smoke command**

Run:

```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; $env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"; D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -m cli.review_command --backend pybullet --scene bench\sim_robot_arm\simple_joint_move_001\scene.json --command bench\sim_robot_arm\simple_joint_move_001\command.json --log-dir logs
```

Expected: command exits 0 and prints a structured decision summary.
