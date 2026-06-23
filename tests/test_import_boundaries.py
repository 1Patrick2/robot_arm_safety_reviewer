"""Capability test: import boundaries and safety invariants."""

import pytest


def test_no_old_top_level_dir_imports():
    """Legacy top-level packages must not be importable or used."""
    forbidden = {"dataset_adapters", "gateway", "runtime_db", "reports", "sim", "robot_safety", "robot_runtime", "robots"}
    import sys
    for mod in list(sys.modules.keys()):
        prefix = mod.split(".")[0]
        if prefix in forbidden:
            pytest.fail(f"Legacy module still loaded: {mod}")


def test_canonical_robot_imports():
    import robot.safety.evaluator
    import robot.runtime.safety_runtime
    import robot.backends.backend_factory
    import robot.adapters.mock_realman_6dof


def test_lerobot_only_in_optional_adapter():
    """lerobot import must not appear in core code."""
    import os
    allowed_paths = {"optional_lerobot_hub_adapter.py", "test_lerobot_hub_smoke.py", "test_import_boundaries.py"}
    for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), "..", "bench")):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            if "import lerobot" in content or "from lerobot" in content:
                if fname not in allowed_paths:
                    pytest.fail(f"lerobot import in unexpected file: {fpath}")
    for root, dirs, files in os.walk(os.path.join(os.path.dirname(__file__), "..", "tests")):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            if "import lerobot" in content or "from lerobot" in content:
                if fname not in allowed_paths:
                    pytest.fail(f"lerobot import in unexpected test file: {fpath}")


def test_ultralytics_not_at_top_level():
    """ultralytics must only be imported lazily inside adapter methods."""
    import ast, inspect
    from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter
    source = inspect.getsource(UltralyticsYoloAdapter)
    tree = ast.parse(source)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name.split(".")[0] for a in node.names] + ([node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else [])
            if "ultralytics" in names:
                pytest.fail(f"ultralytics imported at module level")


def test_llm_not_in_safety_decision_path():
    """SafetyRuntime must not import or reference LLM modules."""
    import inspect
    import robot.runtime.safety_runtime as sr
    source = inspect.getsource(sr)
    assert "diagnostic" not in source
    assert "llm" not in source.lower()
    assert "analysis" not in source.lower()
