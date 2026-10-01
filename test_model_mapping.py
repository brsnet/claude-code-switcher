"""
Simple test to verify model mapping works
"""
from api.model_router import ModelRouter

def test_model_mapping():
    router = ModelRouter()

    # Test Claude model names map to logical names
    print("Testing model name mapping:")
    print(f"claude-opus-5-5 -> {router._normalize_model_name('claude-opus-5-5')}")
    print(f"claude-sonnet-5-5 -> {router._normalize_model_name('claude-sonnet-5-5')}")
    print(f"claude-haiku-3-5 -> {router._normalize_model_name('claude-haiku-3-5')}")
    print(f"opus -> {router._normalize_model_name('opus')}")

    # Test route resolution
    print("\nTesting route resolution (using default routes from .env.example):")
    print(f"opus route: {router.resolve_route('opus')}")
    print(f"sonnet route: {router.resolve_route('sonnet')}")
    print(f"haiku route: {router.resolve_route('haiku')}")
    print(f"claude-opus-5-5 route: {router.resolve_route('claude-opus-5-5')}")

if __name__ == "__main__":
    test_model_mapping()