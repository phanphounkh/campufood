"""CampusEats API entry point."""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.errors import error_body, register_error_handlers
from app.core.security import tokens_match
from app.services.orders import expire_stale_orders

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("campuseats")

UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
# Endpoints that establish a session. They are still protected by the Origin check.
CSRF_EXEMPT_PATHS = {"/api/v1/auth/login", "/api/v1/auth/register"}


async def _expiry_worker() -> None:
    """Expire unpaid orders and release their reserved stock, periodically."""
    while True:
        await asyncio.sleep(settings.expiry_sweep_seconds)
        try:
            async with SessionLocal() as session:
                count = await expire_stale_orders(session)
                if count:
                    logger.info("Expired %d unpaid order(s)", count)
        except Exception:
            logger.exception("Expiry sweep failed")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.media_root.mkdir(parents=True, exist_ok=True)
    task = asyncio.create_task(_expiry_worker()) if settings.run_background_jobs else None
    if settings.demo_payments_enabled:
        logger.warning("DEMO PAYMENTS ENABLED — no real money is collected.")
    yield
    if task:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description=(
        "REST API for **CampusEats**, a student canteen ordering platform.\n\n"
        "* Browser sessions use an HTTP-only `ce_session` cookie. State-changing requests made "
        "with that cookie must echo the `ce_csrf` cookie in the `X-CSRF-Token` header.\n"
        "* Guests access their orders with the `X-Order-Token` header returned at checkout.\n"
        '* Money is exchanged as 2-decimal strings (e.g. `"1.50"`) in USD.\n'
        "* Payments are **demo only**: no real money is transferred."
    ),
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

register_error_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type", settings.csrf_header_name, "X-Order-Token"],
)


@app.middleware("http")
async def csrf_protection(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    if request.method in UNSAFE_METHODS and request.url.path.startswith("/api/"):
        origin = request.headers.get("origin")
        if origin is not None and origin.rstrip("/") not in settings.allowed_origins:
            return JSONResponse(
                error_body("CSRF_FAILED", "Cross-origin request blocked."), status_code=403
            )
        has_session = settings.session_cookie_name in request.cookies
        if has_session and request.url.path not in CSRF_EXEMPT_PATHS:
            header = request.headers.get(settings.csrf_header_name)
            cookie = request.cookies.get(settings.csrf_cookie_name)
            if not tokens_match(header, cookie):
                return JSONResponse(
                    error_body("CSRF_FAILED", "Missing or invalid CSRF token. Please reload."),
                    status_code=403,
                )
    return await call_next(request)


@app.middleware("http")
async def security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("X-Frame-Options", "DENY")
    if request.url.path.startswith("/api/"):
        response.headers.setdefault("Cache-Control", "no-store")
    return response


app.include_router(api_router)

settings.media_root.mkdir(parents=True, exist_ok=True)
app.mount(settings.media_url_prefix, StaticFiles(directory=settings.media_root), name="media")
