"""Contract tests for UltralyticsYoloAdapter.

These tests do **not** require ``ultralytics`` to be installed.
They verify adapter boundary, safety API isolation, and import semantics.
"""

import pytest


class TestUltralyticsYoloAdapterContract:
    def test_missing_ultralytics_raises_clear_error(self):
        """When ultralytics is absent, constructing the adapter must not fail --
        only calling infer() or any method that loads the model should raise."""
        import importlib
        import sys

        # Simulate missing ultralytics by monkeypatching the import
        orig_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__

        def _mock_import(name, *args, **kwargs):
            if name == "ultralytics":
                raise ImportError("No module named 'ultralytics'")
            return orig_import(name, *args, **kwargs)

        try:
            if isinstance(__builtins__, dict):
                __builtins__["__import__"] = _mock_import
            else:
                __builtins__.__import__ = _mock_import

            from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter

            adapter = UltralyticsYoloAdapter("dummy.pt")
            with pytest.raises(RuntimeError, match="ultralytics"):
                adapter._load_model()
        finally:
            if isinstance(__builtins__, dict):
                __builtins__["__import__"] = orig_import
            else:
                __builtins__.__import__ = orig_import

    def test_adapter_class_does_not_import_ultralytics_at_top_level(self):
        """Top-level module import should not trigger ultralytics."""
        import sys
        # Remove any cached import of the adapter module
        for mod in list(sys.modules.keys()):
            if "ultralytics_yolo_adapter" in mod:
                del sys.modules[mod]
        # Fresh import
        from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter  # noqa: PLC0415
        assert "ultralytics" not in sys.modules or "ultralytics" not in str(sys.modules.get("ultralytics"))

    def test_adapter_does_not_expose_forbidden_safety_methods(self):
        from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter  # noqa: PLC0415
        adapter = UltralyticsYoloAdapter("dummy.pt")
        forbidden = {"approve", "reject", "manual_review", "send_action", "execute", "step"}
        adapter_methods = {m for m in dir(adapter) if not m.startswith("_")}
        assert not (forbidden & adapter_methods), f"Found forbidden methods: {forbidden & adapter_methods}"

    def test_adapter_source_has_no_SafetyRuntime_or_RobotDeviceAdapter(self):
        """Check the adapter implementation does not reference runtime types."""
        import inspect
        from perception.adapters.ultralytics_yolo_adapter import UltralyticsYoloAdapter  # noqa: PLC0415
        source = inspect.getsource(UltralyticsYoloAdapter)
        assert "SafetyRuntime" not in source
        assert "RobotDeviceAdapter" not in source
        assert "send_action" not in source
