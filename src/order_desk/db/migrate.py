import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from order_desk.config import settings

logger = logging.getLogger(__name__)

APP_TABLES = frozenset({"customers", "invoices", "garments", "garment_status_events"})
HEAD_REVISION = "a7b87ac7bd0d"


def _alembic_ini_path() -> Path:
    cwd_candidate = Path("alembic.ini")
    if cwd_candidate.is_file():
        return cwd_candidate
    return Path(__file__).resolve().parents[3] / "alembic.ini"


def _build_config() -> Config:
    cfg = Config(str(_alembic_ini_path()))
    cfg.set_main_option("sqlalchemy.url", settings.database_url)
    return cfg


def _table_names(database_url: str) -> set[str]:
    engine = create_engine(database_url)
    try:
        return set(inspect(engine).get_table_names())
    finally:
        engine.dispose()


def _alembic_version(database_url: str) -> str | None:
    tables = _table_names(database_url)
    if "alembic_version" not in tables:
        return None
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            return conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    finally:
        engine.dispose()


def _ensure_audit_table(database_url: str) -> None:
    if "garment_status_events" in _table_names(database_url):
        return
    from order_desk.domains.garments.audit_models import GarmentStatusEventORM

    engine = create_engine(database_url)
    try:
        GarmentStatusEventORM.__table__.create(bind=engine, checkfirst=True)
    finally:
        engine.dispose()


def _bootstrap_legacy_schema(cfg: Config) -> bool:
    """Stamp pre-Alembic databases that were created with create_all()."""
    tables = _table_names(settings.database_url)
    if "customers" not in tables:
        return False

    _ensure_audit_table(settings.database_url)
    tables = _table_names(settings.database_url)
    if not APP_TABLES.issubset(tables):
        return False

    logger.info("Legacy schema detected (pre-Alembic); stamping revision %s", HEAD_REVISION)
    command.stamp(cfg, HEAD_REVISION)
    return True


def upgrade_to_head() -> None:
    cfg = _build_config()
    version = _alembic_version(settings.database_url)
    if version:
        command.upgrade(cfg, "head")
        return

    if _bootstrap_legacy_schema(cfg):
        return

    command.upgrade(cfg, "head")
