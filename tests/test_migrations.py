from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_head_creates_schema(tmp_path):
    db_path = tmp_path / "migrate.db"
    database_url = f"sqlite+pysqlite:///{db_path}"

    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(cfg, "head")

    engine = create_engine(database_url)
    tables = set(inspect(engine).get_table_names())
    assert {
        "alembic_version",
        "customers",
        "invoices",
        "garments",
        "garment_status_events",
    }.issubset(tables)

    with engine.connect() as conn:
        version = conn.exec_driver_sql("SELECT version_num FROM alembic_version").scalar_one()
    assert version == "a7b87ac7bd0d"
