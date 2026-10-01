import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def test_imports():
    try:
        from config.settings import Settings

        print("✓ Settings import successful")
    except Exception as e:
        print(f"✗ Settings import failed: {e}")
        return False

    try:
        from api.model_router import ModelRouter

        print("✓ ModelRouter import successful")
    except Exception as e:
        print(f"✗ ModelRouter import failed: {e}")
        return False

    try:
        from api.services import RequestHandler

        print("✓ RequestHandler import successful")
    except Exception as e:
        print(f"✗ RequestHandler import failed: {e}")
        return False

    try:
        from providers.registry import ProviderRegistry

        print("✓ ProviderRegistry import successful")
    except Exception as e:
        print(f"✗ ProviderRegistry import failed: {e}")
        return False

    return True


if __name__ == "__main__":
    if test_imports():
        print("\n✓ All imports successful!")
    else:
        print("\n✗ Some imports failed!")
        sys.exit(1)
