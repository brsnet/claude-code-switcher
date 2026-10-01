"""
Basic tests for the Claude Code Switcher.
"""
import pytest
from config.settings import Settings
from api.model_router import ModelRouter

def test_settings_nvidia_models():
    """Test that NVIDIA models are discovered correctly."""
    # This test would need mocked environment variables
    pass

def test_model_router_resolve_route():
    """Test route resolution."""
    router = ModelRouter()
    # Test with empty settings
    candidates = router.resolve_route("opus")
    assert isinstance(candidates, list)

if __name__ == "__main__":
    pytest.main([__file__])