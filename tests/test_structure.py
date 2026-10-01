import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from config.settings import Settings
from api.model_router import ModelRouter


def test_settings_initialization():
    """Test that settings can be initialized without error."""
    settings = Settings()
    assert settings is not None
    print("✓ Settings initialized successfully")


def test_model_router_initialization():
    """Test that model router can be initialized."""
    router = ModelRouter()
    assert router is not None
    print("✓ Model router initialized successfully")


def test_resolve_route_empty():
    """Test resolving routes with empty configuration."""
    router = ModelRouter()
    # With empty settings, we should get empty lists
    opus_candidates = router.resolve_route("opus")
    sonnet_candidates = router.resolve_route("sonnet")
    haiku_candidates = router.resolve_route("haiku")

    assert isinstance(opus_candidates, list)
    assert isinstance(sonnet_candidates, list)
    assert isinstance(haiku_candidates, list)
    print("✓ Route resolution works with empty configuration")


if __name__ == "__main__":
    test_settings_initialization()
    test_model_router_initialization()
    test_resolve_route_empty()
    print("All basic tests passed!")
