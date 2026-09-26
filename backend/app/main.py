"""LegalLens AI backend entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import analyze, ask, auth, compare, documents, evidence, seed
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import rate_limiter
from app.db import init_db

log = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    settings.validate_for_production()
    init_db()
    log.info("startup", extra={"ctx": {"env": settings.env, "llm_provider": settings.llm_provider}})
    yield


app = FastAPI(
    title="LegalLens AI",
    description="Evidence-grounded legal document assistant. Provides legal information and "
    "document assistance; not a substitute for a qualified legal professional.",
    version="0.1.0",
    lifespan=lifespan,
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    log.error("unhandled_exception", extra={"ctx": {"path": request.url.path, "error": str(exc)}})
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


@app.get("/api/health", dependencies=[Depends(rate_limiter("default"))])
def health() -> dict:
    return {"status": "ok", "service": "LegalLens AI", "llm_provider": get_settings().llm_provider}


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(ask.router)
app.include_router(analyze.router)
app.include_router(compare.router)
app.include_router(evidence.router)
app.include_router(seed.router)
