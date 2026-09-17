import logging
import sys

from order_desk.config import settings


def configure_logging() -> None:
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    root = logging.getLogger()
    if not root.handlers:
        logging.basicConfig(
            level=level,
            format="%(message)s",
            stream=sys.stdout,
        )
    else:
        root.setLevel(level)
    logging.getLogger("order_desk.request").setLevel(level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
