from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from order_desk.config import settings
from order_desk.db.session import init_db
from order_desk.logging_config import configure_logging
from order_desk.middleware import RequestLoggingMiddleware
from order_desk.domains.customers.router import router as customers_router
from order_desk.domains.garments.router import router as garments_router
from order_desk.domains.invoices.router import router as invoices_router
from order_desk.domains.status_lifecycle.router import router as status_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    init_db()
    yield


_openapi_disabled = settings.disable_openapi
app = FastAPI(
    title="Order Desk API",
    description="Internal dry cleaning order management",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if _openapi_disabled else "/docs",
    redoc_url=None if _openapi_disabled else "/redoc",
    openapi_url=None if _openapi_disabled else "/openapi.json",
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
default_origins = ["http://localhost:5174", "http://127.0.0.1:5174"]
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or default_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "X-Operator-Id", "X-Request-Id"],
    expose_headers=["X-Request-Id"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"ok": "true", "service": "order-desk-api"}


app.include_router(customers_router, prefix="/api/v1")
app.include_router(invoices_router, prefix="/api/v1")
app.include_router(garments_router, prefix="/api/v1")
app.include_router(status_router, prefix="/api/v1")
