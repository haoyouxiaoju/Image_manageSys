import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.core.config import Settings

logger = logging.getLogger("app.middleware")


class RequestContextMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, request_id_header: str) -> None:
        super().__init__(app)
        self.request_id_header = request_id_header

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(self.request_id_header) or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[self.request_id_header] = request_id
        return response


class JwtHeaderMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, auth_header_name: str) -> None:
        super().__init__(app)
        self.auth_header_name = auth_header_name

    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get(self.auth_header_name)
        if auth_header:
            if not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": {
                            "code": "INVALID_AUTH_HEADER",
                            "message": "Authorization header must use Bearer token format.",
                        }
                    },
                )
            token = auth_header.removeprefix("Bearer ").strip()
            if not token:
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": {
                            "code": "EMPTY_TOKEN",
                            "message": "Bearer token cannot be empty.",
                        }
                    },
                )
            request.state.access_token = token
        return await call_next(request)


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = (perf_counter() - start) * 1000
        response.headers["X-Process-Time-MS"] = f"{elapsed_ms:.2f}"

        request_id = getattr(request.state, "request_id", "unknown")
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response


def register_middleware(app: FastAPI, app_settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware, request_id_header=app_settings.request_id_header)
    app.add_middleware(JwtHeaderMiddleware, auth_header_name=app_settings.auth_header_name)
    app.add_middleware(RequestMetricsMiddleware)

