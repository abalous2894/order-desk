def test_openapi_enabled_by_default_in_tests(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_disable_openapi_setting():
    from order_desk.config import Settings

    settings = Settings(
        database_url="sqlite+pysqlite:///:memory:",
        operator_token="test",
        disable_openapi=True,
    )
    assert settings.disable_openapi is True
