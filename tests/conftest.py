import os

# Use in-memory SQLite before any order_desk imports bind a production engine.
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["OPERATOR_TOKEN"] = "test-operator-token"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from order_desk.db.base import Base
from order_desk.db.session import get_db
from order_desk.domains.customers import models as _customer_models  # noqa: F401
from order_desk.domains.garments import audit_models as _garment_audit_models  # noqa: F401
from order_desk.domains.garments import models as _garment_models  # noqa: F401
from order_desk.domains.invoices import models as _invoice_models  # noqa: F401
from order_desk.main import app

_test_engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
Base.metadata.create_all(_test_engine)
TestingSessionLocal = sessionmaker(bind=_test_engine, autoflush=False, autocommit=False)

AUTH_HEADERS = {
    "Authorization": "Bearer test-operator-token",
    "X-Operator-Id": "AUDIT01",
}


@pytest.fixture
def auth_headers():
    return dict(AUTH_HEADERS)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


def _with_auth_headers(kwargs: dict) -> dict:
    headers = {**AUTH_HEADERS, **kwargs.pop("headers", {})}
    kwargs["headers"] = headers
    return kwargs


@pytest.fixture
def client(db_session, monkeypatch):
    monkeypatch.setattr("order_desk.db.session.init_db", lambda: None)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        original_post = test_client.post
        original_patch = test_client.patch

        def authed_post(*args, **kwargs):
            return original_post(*args, **_with_auth_headers(kwargs))

        def authed_patch(*args, **kwargs):
            return original_patch(*args, **_with_auth_headers(kwargs))

        test_client.post = authed_post  # type: ignore[method-assign]
        test_client.patch = authed_patch  # type: ignore[method-assign]
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def bare_client(db_session, monkeypatch):
    """TestClient without automatic operator auth headers."""
    monkeypatch.setattr("order_desk.db.session.init_db", lambda: None)

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clean_tables(db_session):
    for table in reversed(Base.metadata.sorted_tables):
        db_session.execute(table.delete())
    db_session.commit()
    yield
