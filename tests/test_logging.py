import json
import logging
from unittest.mock import patch

from conftest import AUTH_HEADERS


def test_response_includes_request_id(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("X-Request-Id")


def test_client_request_id_is_echoed(client):
    request_id = "test-correlation-id-12345"
    res = client.get("/health", headers={"X-Request-Id": request_id})
    assert res.headers.get("X-Request-Id") == request_id


def test_mutating_request_logs_structured_entry(client):
    with patch("order_desk.middleware.request_logging.logger") as mock_logger:
        res = client.post(
            "/api/v1/customers/get-or-create",
            json={"name": "Log Test", "phone": "555-7700"},
            headers={**AUTH_HEADERS, "X-Request-Id": "log-req-1"},
        )
        assert res.status_code == 200
        assert mock_logger.info.called
        payload = json.loads(mock_logger.info.call_args[0][0])
        assert payload["event"] == "http_request"
        assert payload["request_id"] == "log-req-1"
        assert payload["operator_id"] == AUTH_HEADERS["X-Operator-Id"]
        assert payload["path"] == "/api/v1/customers/get-or-create"
        assert payload["outcome"] == "success"
