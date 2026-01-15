import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config import settings
from app.routes.api import router as api_router
from app.routes.feedback import router as feedback_router
from app.routes.pages import router as pages_router
from app.security.exceptions import add_exception_handlers
from app.security.headers import BodySizeLimitMiddleware, HTTPSRedirectMiddleware, SecurityHeadersMiddleware

logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title=settings.app_name,
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(BodySizeLimitMiddleware, max_body_bytes=settings.max_body_bytes)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    session_cookie=settings.session_cookie,
    max_age=settings.session_max_age,
    same_site=settings.csrf_cookie_samesite,
    https_only=settings.secure_cookies,
)
app.add_middleware(HTTPSRedirectMiddleware, enabled=settings.https_redirect_enabled)
app.add_middleware(SecurityHeadersMiddleware)
if settings.cors_allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["POST"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )

add_exception_handlers(app)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages_router)
app.include_router(api_router)
app.include_router(feedback_router)
