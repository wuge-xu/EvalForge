import json
import logging

from evalforge.core.logging import (
    JsonFormatter,
    RequestContextFilter,
    get_request_id,
    reset_request_id,
    set_request_id,
)


def test_json_formatter_includes_request_context_and_extra_fields() -> None:
    token = set_request_id("req-unit-001")

    try:
        record = logging.LogRecord(
            name="evalforge.test",
            level=logging.INFO,
            pathname=__file__,
            lineno=20,
            msg="experiment_started",
            args=(),
            exc_info=None,
        )
        record.experiment_id = "exp-001"
        RequestContextFilter().filter(record)

        payload = json.loads(JsonFormatter().format(record))
    finally:
        reset_request_id(token)

    assert payload["level"] == "INFO"
    assert payload["logger"] == "evalforge.test"
    assert payload["message"] == "experiment_started"
    assert payload["request_id"] == "req-unit-001"
    assert payload["experiment_id"] == "exp-001"
    assert get_request_id() == "-"


def test_json_formatter_converts_non_serializable_values_to_string() -> None:
    record = logging.LogRecord(
        name="evalforge.test",
        level=logging.INFO,
        pathname=__file__,
        lineno=48,
        msg="value_logged",
        args=(),
        exc_info=None,
    )
    record.custom_value = object()

    payload = json.loads(JsonFormatter().format(record))

    assert isinstance(payload["custom_value"], str)
