"""Factory for simulation review backends."""

from __future__ import annotations

from .mock_backend import MockGeometryBackend

'''按照名字创建后端，目前支持 "mock" 和 "pybullet" 两种后端。用户可以通过传入不同的名字来选择使用哪个后端进行碰撞检查和轨迹回放。这个工厂函数的好处是隐藏了后端的具体实现细节，用户只需要关心接口和功能，而不需要直接依赖某个特定的后端类。未来如果我们想添加更多的后端，比如基于 MuJoCo 的后端，我们只需要在这里扩展一下工厂函数，而不需要修改其他使用后端的代码。'''
def create_backend(name: str):
    normalized = name.strip().lower()
    if normalized == "mock":
        return MockGeometryBackend()
    if normalized == "pybullet":
        # 延迟导入 PyBullet 后端，只有在用户选择时才导入，这样可以避免不必要的依赖和加快启动速度
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
