from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from order_desk.config import settings
from order_desk.db.migrate import upgrade_to_head


def test_upgrade_bootstraps_legacy_create_all_schema(tmp_path, monkeypatch):
    db_path = tmp_path / "legacy.db"
    database_url = f"sqlite+pysqlite:///{db_path}"
    monkeypatch.setattr(settings, "database_url", database_url)

    engine = create_engine(database_url)
    from order_desk.db.base import Base
    from order_desk.domains.customers import models as customer_models  # noqa: F401
    from order_desk.domains.garments import models as garment_models  # noqa: F401
    from order_desk.domains.invoices import models as invoice_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    engine.dispose()

    tables_before = set(inspect(create_engine(database_url)).get_table_names())
    assert "customers" in tables_before
    assert "alembic_version" not in tables_before

    upgrade_to_head()

    engine = create_engine(database_url)
    tables_after = set(inspect(engine).get_table_names())
    with engine.connect() as conn:
        version = conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one()
    engine.dispose()

    assert version == "a7b87ac7bd0d"
    assert "garment_status_events" in tables_after

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")
