import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import admin, auth, health, orders, products
from app.core.config import settings
from app.db.session import engine, init_dev_schema
from app.models import entities  # noqa: F401 - register models

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO),
                    format="%(asctime)s %(levelname)s %(name)s %(message)s")
# httpx/httpcore log request URLs, and Telegram Bot API URLs contain the bot token.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_production_secrets()
    await init_dev_schema()  # SQLite dev only; PostgreSQL uses `alembic upgrade head`
    yield
    await engine.dispose()


app = FastAPI(title=settings.app_name, version="0.2.0",
              description="StarMarket API. Payments are confirmed manually by an administrator.",
              lifespan=lifespan,
              docs_url=None if settings.app_env.lower() == "production" else "/docs",
              redoc_url=None, openapi_url=None if settings.app_env.lower() == "production" else "/openapi.json")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=False,
                   allow_methods=["GET", "POST", "PATCH"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key"])


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    return response


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logging.getLogger("starmarket").exception("Unhandled error path=%s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Server error. Please try again later."})


for r in (health.router, auth.router, products.router, orders.router, admin.router):
    app.include_router(r, prefix=settings.api_v1_prefix)

# Static front-ends: Mini App at /app/, admin UI at /admin-ui/ (admin API still checks Telegram ID on every call).
if (WEB_DIR / "miniapp").is_dir():
    app.mount("/app", StaticFiles(directory=WEB_DIR / "miniapp", html=True), name="miniapp")
if (WEB_DIR / "admin").is_dir():
    app.mount("/admin-ui", StaticFiles(directory=WEB_DIR / "admin", html=True), name="admin-ui")


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse("/app/")
