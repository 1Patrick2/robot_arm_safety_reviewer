# Stage 2.4 Backend Diagnostics Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the mock and PyBullet backends reproducible, diagnosable, and ready for backend comparison.

**Architecture:** Keep Stage 2.4 focused on diagnostic infrastructure. First document the Windows PyBullet setup and OpenBLAS workaround, then enrich backend metadata in logs and reports. Follow-up tasks can add PyBullet smoke benchmark mode and `compare_backends.py`.

**Tech Stack:** Python 3.10, pytest, micromamba, PyBullet optional backend, existing gateway logs and Markdown reports.

---

### Task 1: Windows PyBullet Setup Documentation

**Files:**
- Create: `docs/windows_pybullet_setup.md`
- Modify: `README.md`

**Steps:**
1. Document the recommended Windows environment: PowerShell, micromamba, Python 3.10, `pybullet`, `pytest`, `matplotlib-base`.
2. Explain why global Windows Python 3.12 plus `pip install pybullet` is not recommended.
3. Document the OpenBLAS workaround for NumPy/Matplotlib native crashes:
   ```powershell
   micromamba install -n robotarm-pybullet -c conda-forge "libblas=*=*openblas" -y
   ```
4. Document project-local pytest temp setup:
   ```powershell
   New-Item -ItemType Directory -Force .pytest_tmp | Out-Null
   $env:TEMP="$PWD\.pytest_tmp"
   $env:TMP="$PWD\.pytest_tmp"
   ```
5. Link the new document from README.

**Verification:**
Run:
```powershell
Select-String -Path README.md -Pattern "windows_pybullet_setup"
Select-String -Path docs\windows_pybullet_setup.md -Pattern "OpenBLAS"
```

---

### Task 2: Backend Metadata in Logs and Reports

**Files:**
- Modify: `sim/mock_backend.py`
- Modify: `sim/pybullet_backend.py`
- Modify: `gateway/safety_gate.py`
- Modify: `reports/report_writer.py`
- Test: `tests/test_stage2_backend_metadata.py`

**Steps:**
1. Write tests that `review_only(..., backend_name="mock")` logs mock backend metadata including `collision_method`.
2. Write tests that `review_only(..., backend_name="pybullet")` logs PyBullet metadata including `mode`, `urdf_path`, `collision_method`, `fidelity`, and `notes`.
3. Write a report test asserting the Markdown report contains a `Review Backend` section.
4. Update backend metadata helpers to preserve the backend result metadata in `review_backend`.
5. Add `fidelity` and `notes` to the PyBullet backend metadata.
6. Add the report section.

**Verification:**
Run:
```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage2_backend_metadata.py -q --basetemp .pytest_tmp/current
```

---

### Task 3: Full Verification

**Files:**
- No extra production files unless tests reveal a gap.

**Steps:**
1. Run the full test suite.
2. Run the mock benchmark.
3. Run a PyBullet smoke command.

**Verification:**
Run:
```powershell
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp/current
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.run_benchmark --backend mock --bench bench\sim_robot_arm --log-dir logs\benchmark --output-json output_reports\stage1_benchmark_summary.json --output-md output_reports\stage1_benchmark_summary.md
$env:TEMP="$PWD\.pytest_tmp"; $env:TMP="$PWD\.pytest_tmp"; D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m cli.review_command --backend pybullet --scene bench\sim_robot_arm\simple_joint_move_001\scene.json --command bench\sim_robot_arm\simple_joint_move_001\command.json --log-dir logs
```

---

## Deferred Stage 2.4 Follow-ups

- PyBullet smoke benchmark mode that validates structured outputs without scoring against `expected.json`.
- `cli.compare_backends` with diagnosis labels.
- Backend comparison JSON and Markdown report.
- `docs/stage2_backend_diagnostics.md` generated from comparison results.

Do not implement full PyBullet `getClosestPoints`, GUI replay, RealMan SDK, ROS2/MoveIt, or Agent/LLM integration in this stage.

