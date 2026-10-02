def test_imports():
    from api.model_router import ModelRouter
    from api.services import RequestHandler
    from config.settings import Settings
    from providers.registry import ProviderRegistry

    assert Settings is not None
    assert ModelRouter is not None
    assert RequestHandler is not None
    assert ProviderRegistry is not None
