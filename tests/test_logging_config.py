import logging

from config.logging_config import configure_application_logging


def test_application_info_logs_are_written_to_terminal(capsys):
    configure_application_logging()

    logging.getLogger("api.services").info("ROUTE: provider=groq model='example-model'")

    captured = capsys.readouterr()
    assert "INFO" in captured.err
    assert "provider=groq" in captured.err
    assert "model='example-model'" in captured.err


def test_logging_configuration_is_idempotent():
    configure_application_logging()
    configure_application_logging()

    handlers = [
        handler
        for handler in logging.getLogger("api").handlers
        if handler.name == "claude_code_switcher_terminal"
    ]
    assert len(handlers) == 1
