import pytest

from sim.backend_factory import create_backend


def test_create_mock_backend():
    backend = create_backend("mock")

    assert backend.name == "mock"


def test_create_backend_rejects_unknown_name():
    with pytest.raises(ValueError, match="unsupported simulation backend"):
        create_backend("unknown")
