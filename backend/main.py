from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.v1.validate import router as validate_router
from api.v1.ventures import router as ventures_router
from core.config import settings
from core.logging import configure_logging
from utils.responses import error

configure_logging()

app = FastAPI(title="VentureMind AI API")

# CORS per anchor.md/SECURITY.md — only trusted origins, never "*"
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Every /api/v1 error response uses the same envelope as success responses
# (utils/responses.py) — see anchor.md/ARCHITECTURE.md > API STRUCTURE.
_STATUS_CODES = {
    400: "VALIDATION_ERROR",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    409: "CONFLICT",
    422: "VALIDATION_ERROR",
}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = _STATUS_CODES.get(exc.status_code, "ERROR")
    return JSONResponse(status_code=exc.status_code, content=error(str(exc.detail), code))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content=error(str(exc.errors()), "VALIDATION_ERROR"))


app.include_router(ventures_router, prefix="/api/v1")
app.include_router(validate_router, prefix="/api/v1")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
