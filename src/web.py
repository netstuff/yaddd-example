from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from yaddd import (
    BusinessRuleViolationError,
    InvariantViolationError,
    ValidationError,
)

from api.routes import router
from composition_root import CompositionRoot
from config import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    root = CompositionRoot(settings)
    await root.init_db()
    app.state.composition_root = root
    yield
    await root.dispose()


app = FastAPI(title=settings.app.name, lifespan=lifespan)
app.include_router(router)


@app.exception_handler(InvariantViolationError)
@app.exception_handler(BusinessRuleViolationError)
@app.exception_handler(ValidationError)
async def _handle_domain_errors(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})
