from __future__ import annotations

import asyncio
import json
import secrets
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response, StreamingResponse
from pydantic import Field

from .artifacts import ArtifactError
from .comparison import ComparisonError
from .models import StrictModel
from .service import CampaignService, ServiceError


MAX_REQUEST_BYTES = 1024 * 1024
MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


class StartingPreset(StrictModel):
    id: str = Field(min_length=1, max_length=64, pattern=r"^[a-z0-9][a-z0-9-]*$")
    version: int = Field(ge=1)


class PlanValidationRequest(StrictModel):
    plan: dict[str, Any]
    starting_preset: StartingPreset | None = None


class RunCreateRequest(PlanValidationRequest):
    plan_hash: str = Field(min_length=1, max_length=128)
    client_request_id: str = Field(min_length=1, max_length=128)


class SettingsUpdateRequest(StrictModel):
    test_workspace_root: str = Field(min_length=1)


class ComparisonRequest(StrictModel):
    reference_run_id: str = Field(min_length=1, max_length=64)
    candidate_run_id: str = Field(min_length=1, max_length=64)
    descriptive_override: bool = False


def create_app(
    service: CampaignService,
    *,
    authority: str,
    web_dist: Path | None = None,
    check_product_on_startup: bool = True,
) -> FastAPI:
    if not authority or "/" in authority:
        raise ValueError("authority must be a host[:port]")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if check_product_on_startup:
            await asyncio.to_thread(service.refresh_product_catalog)
        try:
            yield
        finally:
            await service.shutdown()

    app = FastAPI(title="EphemeralOS Benchmark", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def security(request: Request, call_next):
        request_id = secrets.token_hex(12)
        request.state.request_id = request_id
        host = request.headers.get("host", "")
        if host != authority:
            return _error(400, "invalid_host", "request Host does not match the server authority", request_id)
        if request.method in MUTATION_METHODS:
            if request.headers.get("origin") != f"http://{authority}":
                return _error(403, "invalid_origin", "mutation Origin must match the server origin", request_id)
            supplied = request.headers.get("x-eos-benchmark-nonce", "")
            if not secrets.compare_digest(supplied, service.nonce):
                return _error(403, "invalid_nonce", "mutation nonce is missing or invalid", request_id)
            media_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
            if media_type != "application/json":
                return _error(415, "json_required", "mutations require application/json", request_id)
            length = request.headers.get("content-length")
            if length is not None:
                try:
                    if int(length) > MAX_REQUEST_BYTES:
                        return _error(413, "body_too_large", "request body exceeds one MiB", request_id)
                except ValueError:
                    return _error(400, "invalid_content_length", "Content-Length is invalid", request_id)
            body = await request.body()
            if len(body) > MAX_REQUEST_BYTES:
                return _error(413, "body_too_large", "request body exceeds one MiB", request_id)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        if request.url.path.startswith("/api/") or request.url.path == "/":
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ServiceError)
    async def service_error(request: Request, error: ServiceError):
        return _error(error.status, error.code, str(error), request.state.request_id, error.details)

    async def artifact_error(request: Request, error: Exception):
        return _error(404, "not_found", str(error), request.state.request_id)

    app.add_exception_handler(ArtifactError, artifact_error)
    app.add_exception_handler(ComparisonError, artifact_error)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        return _error(422, "invalid_request", "the request body is invalid", request.state.request_id, error.errors())

    @app.get("/api/v1/health")
    async def health():
        return service.health()

    @app.get("/api/v1/settings")
    async def settings():
        return service.settings()

    @app.put("/api/v1/settings")
    async def update_settings(body: SettingsUpdateRequest):
        return service.update_settings(body.test_workspace_root)

    @app.get("/api/v1/definitions")
    async def definitions():
        return service.definitions()

    @app.post("/api/v1/plans/validate")
    async def validate_plan(body: PlanValidationRequest):
        return service.validate_plan(body.plan)

    @app.post("/api/v1/runs", status_code=202)
    async def create_run(body: RunCreateRequest):
        starting_preset = body.starting_preset.model_dump(mode="json") if body.starting_preset else None
        return await service.create_run(
            body.plan, body.plan_hash, body.client_request_id, starting_preset
        )

    @app.get("/api/v1/runs")
    async def list_runs(cursor: str | None = None):
        if cursor is not None:
            raise ServiceError(400, "invalid_cursor", "pagination cursors are not currently issued")
        return service.list_runs()

    @app.get("/api/v1/runs/{run_id}")
    async def run(run_id: str):
        return service.run(run_id)

    @app.post("/api/v1/runs/{run_id}/cancel", status_code=202)
    async def cancel(run_id: str):
        return await service.cancel(run_id)

    @app.get("/api/v1/runs/{run_id}/report")
    async def report(run_id: str):
        return service.report(run_id)

    @app.get("/api/v1/runs/{run_id}/artifacts")
    async def artifacts(run_id: str):
        return service.artifacts(run_id)

    @app.get("/api/v1/runs/{run_id}/artifacts/{artifact_id}")
    async def artifact(run_id: str, artifact_id: str):
        return service.artifact(run_id, artifact_id)

    @app.post("/api/v1/compare")
    async def compare(body: ComparisonRequest):
        return service.compare(body.reference_run_id, body.candidate_run_id, body.descriptive_override)

    @app.get("/api/v1/runs/{run_id}/events")
    async def events(request: Request, run_id: str):
        raw = request.headers.get("last-event-id", "0")
        try:
            after = int(raw)
            if after < 0:
                raise ValueError
        except ValueError as error:
            raise ServiceError(400, "invalid_last_event_id", "Last-Event-ID must be a non-negative integer") from error

        async def frames():
            async for record in service.events(run_id, after):
                if record.get("heartbeat"):
                    yield ": keep-alive\n\n"
                    continue
                payload = json.dumps(record, separators=(",", ":"), ensure_ascii=False)
                yield f"id: {record['sequence']}\nevent: {record['data']['kind']}\ndata: {payload}\n\n"

        return StreamingResponse(
            frames(), media_type="text/event-stream",
            headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
        )

    if web_dist is not None:
        dist = web_dist.resolve(strict=True)
        index = dist / "index.html"
        if not index.is_file() or index.is_symlink():
            raise ValueError("web distribution is missing index.html")
        nonce_placeholder = '<meta name="eos-benchmark-nonce" content="" />'
        index_template = index.read_text()
        if index_template.count(nonce_placeholder) != 1:
            raise ValueError("web distribution must contain exactly one mutation nonce placeholder")

        @app.get("/assets/{asset_path:path}")
        async def asset(asset_path: str):
            path = (dist / "assets" / asset_path).resolve(strict=False)
            assets = (dist / "assets").resolve(strict=False)
            if not path.is_relative_to(assets) or path.is_symlink() or not path.is_file():
                return _error(404, "not_found", "asset not found", secrets.token_hex(12))
            return FileResponse(path, headers={"Cache-Control": "public, max-age=31536000, immutable"})

        @app.get("/{route:path}")
        async def spa(route: str):
            if route.startswith("api/"):
                return _error(404, "not_found", "API route not found", secrets.token_hex(12))
            bootstrap = f'<meta name="eos-benchmark-nonce" content="{service.nonce}" />'
            content = index_template.replace(nonce_placeholder, bootstrap, 1)
            return HTMLResponse(content, headers={
                "Cache-Control": "no-store",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data:",
            })

    return app


def _error(
    status: int, code: str, message: str, request_id: str, details: Any = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "details": details, "request_id": request_id}},
        headers={"Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"},
    )
