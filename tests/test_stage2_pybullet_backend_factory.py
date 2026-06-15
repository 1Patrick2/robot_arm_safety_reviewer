import builtins

import pytest

from sim.backend_factory import create_backend


def test_create_pybullet_backend_when_pybullet_available():
    pytest.importorskip("pybullet")

    backend = create_backend("pybullet")

    assert backend.name == "pybullet"


def test_create_pybullet_backend_reports_missing_dependency(monkeypatch):
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "pybullet":
            raise ImportError("simulated missing pybullet")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RuntimeError, match="PyBullet backend requires optional dependency"):
        create_backend("pybullet")
