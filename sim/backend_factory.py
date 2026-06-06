"""Factory for simulation review backends."""

from __future__ import annotations

from .mock_backend import MockGeometryBackend


def create_backend(name: str):
    normalized = name.strip().lower()
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
