# Windows PyBullet Setup

This project can run the core mock backend without PyBullet. PyBullet is an optional Stage 2 simulation backend for URDF loading and trajectory replay.

## Recommended Environment

Use Windows PowerShell with micromamba, Python 3.10, and packages from `conda-forge`:

```powershell
$env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"
D:\YJSXueXi\Software\micromamba\micromamba.exe create -n robotarm-pybullet -c conda-forge python=3.10 pybullet pytest matplotlib-base -y
```

Run commands without activating the environment:

```powershell
$env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"
D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python --version
D:\YJSXueXi\Software\micromamba\micromamba.exe run -n robotarm-pybullet python -c "import pybullet as p; print('pybullet ok')"
```

You can also call the environment Python directly:

```powershell
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest -q
```

## Why Not Global Python 3.12

Avoid installing PyBullet into a global Windows Python 3.12 environment. PyBullet may not have a compatible wheel for that stack and can fall back to a source build that requires Microsoft C++ Build Tools. Conda-forge provides prebuilt Windows packages for PyBullet and its native dependencies.

## OpenBLAS Workaround

On some Windows environments, the default MKL-backed NumPy stack can crash in `numpy.linalg` or Matplotlib 3D plotting. If you see a native crash such as `Windows fatal exception` from `numpy.linalg.inv`, switch the environment to OpenBLAS:

```powershell
$env:MAMBA_ROOT_PREFIX="D:\YJSXueXi\Software\micromamba_root"
D:\YJSXueXi\Software\micromamba\micromamba.exe install -n robotarm-pybullet -c conda-forge "libblas=*=*openblas" -y
```

Verify NumPy and the plot-capable test:

```powershell
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -c "import numpy as np; print(np.linalg.inv(np.eye(4)))"
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest tests/test_stage1_reports.py::test_write_3d_plot_creates_png_when_matplotlib_available -q --basetemp .pytest_tmp/plot
```

## Pytest Temp Directory

If pytest cannot access the default Windows temp directory, use a project-local temp directory:

```powershell
New-Item -ItemType Directory -Force .pytest_tmp | Out-Null
$env:TEMP="$PWD\.pytest_tmp"
$env:TMP="$PWD\.pytest_tmp"
```

Use `--basetemp` to avoid scanning stale pytest temp folders:

```powershell
D:\YJSXueXi\Software\micromamba_root\envs\robotarm-pybullet\python.exe -m pytest -q --basetemp .pytest_tmp/current
```

## Dependency Boundary

- `mock` backend: required baseline, no PyBullet dependency.
- `pybullet` backend: optional Stage 2 backend, requires PyBullet.
- `matplotlib-base`: optional, used for PNG visualization.
- `requirements-sim.txt`: simulation-only pip dependency list for Linux or WSL workflows. On Windows, prefer conda-forge for PyBullet.

