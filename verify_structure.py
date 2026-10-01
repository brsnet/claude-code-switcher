"""
Simple test to verify the application can start.
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

def test_basic_imports():
    """Test that we can import the main modules."""
    try:
        print("Testing config import...")
        from config import settings
        print("✓ Config imported successfully")

        print("Testing model_router import...")
        from api.model_router import ModelRouter
        print("✓ ModelRouter imported successfully")

        print("Testing services import...")
        from api.services import RequestHandler
        print("✓ RequestHandler imported successfully")

        print("Testing providers registry...")
        from providers.registry import ProviderRegistry
        print("✓ ProviderRegistry imported successfully")

        print("Testing routes import...")
        from api.routes import app
        print("✓ Routes imported successfully")

        print("\n✓ All basic imports successful!")
        return True

    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_basic_imports()
    if success:
        print("\nApplication structure is sound!")
    else:
        print("\nApplication has import issues!")
        sys.exit(1)