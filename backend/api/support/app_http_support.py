from __future__ import annotations

import time

from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import JSONResponse

from backend.api.support.runtime_common import ApiError


AUTH_EXEMPT_API_PATHS = frozenset(
    {
        "/api/auth/session",
        "/api/auth/session/import",
        "/api/auth/sign-in",
        "/api/auth/sign-up",
        "/api/auth/sign-out",
        "/api/auth/password-reset",
        "/api/auth/invitations/preview",
        "/api/auth/invitations/preview-by-email",
        "/api/auth/invitations/accept",
    }
)


def _auth_error_response(*, status_code: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message}},
    )


async def add_request_id_and_log_slow_requests(request: Request, call_next):
    from backend.api import app as app_module

    request_id = app_module.ensure_request_id(request)
    started = time.perf_counter()
    status_code: int | None = None
    response: Response | None = None
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    except Exception:
        duration = time.perf_counter() - started
        app_module.HTTP_PERF_LOGGER.exception(
            "HTTP_ERROR path=%s method=%s status=%s duration=%.3f request_id=%s query=%s",
            request.url.path,
            request.method,
            status_code,
            duration,
            request_id,
            dict(request.query_params),
        )
        raise
    finally:
        duration = time.perf_counter() - started
        if duration >= app_module.SLOW_HTTP_REQUEST_SEC:
            app_module.HTTP_PERF_LOGGER.warning(
                "HTTP_SLOW path=%s method=%s status=%s duration=%.3f request_id=%s query=%s",
                request.url.path,
                request.method,
                status_code,
                duration,
                request_id,
                dict(request.query_params),
            )
        if response is not None:
            response.headers["X-Request-ID"] = request_id


async def disable_app_asset_cache(request: Request, call_next):
    response = await call_next(request)
    if request.url.path == "/app" or request.url.path.startswith("/app/"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


async def enforce_phase2_auth(request: Request, call_next):
    from backend.api import app as app_module

    if not app_module.auth_is_enabled():
        return await call_next(request)
    if not request.url.path.startswith("/api/"):
        return await call_next(request)
    if request.url.path in app_module.AUTH_EXEMPT_API_PATHS:
        return await call_next(request)

    auth_context = app_module.read_auth_context(request)
    if auth_context is None:
        return app_module._auth_error_response(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code="unauthorized",
            message="Authentication required.",
        )
    if not auth_context.authorized:
        return app_module._auth_error_response(
            status_code=status.HTTP_403_FORBIDDEN,
            code="forbidden",
            message="This account is not authorized for the console.",
        )

    request.state.auth_context = auth_context
    return await call_next(request)


def handle_api_error(_request: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}},
    )
