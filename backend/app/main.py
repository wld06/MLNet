from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import cleaning, datasets, deploy, experiments, runs
from app.core.exceptions import (
    DatasetNotFoundError,
    DatasetTooLargeError,
    DatasetVersionNotFoundError,
    ExperimentNotFoundError,
    InvalidOperationError,
    MLNestException,
    RunNotFoundError,
    StorageError
)

app = FastAPI(
    title="MLNest",
    version="0.1.0",
    description="Open source ML training and deployment platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router, prefix="/api")
app.include_router(cleaning.router, prefix="/api")
app.include_router(experiments.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
app.include_router(deploy.router, prefix="/api")

@app.exception_handler(DatasetNotFoundError)
@app.exception_handler(DatasetVersionNotFoundError)
@app.exception_handler(ExperimentNotFoundError)
@app.exception_handler(RunNotFoundError)
async def not_found_handler(request: Request, exc: MLNestException) -> JSONResponse:
    return JSONResponse(status_code=404, content={"detail":str(exc)})

@app.exception_handler(DatasetTooLargeError)
async def too_large_handler(request: Request, exc: DatasetTooLargeError) -> JSONResponse:
    return JSONResponse(status_code=413, content={"detail":str(exc)})

@app.exception_handler(InvalidOperationError)
async def invalid_op_handler(request: Request, exc: InvalidOperationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc)})

@app.exception_handler(StorageError)
async def storage_error_handler(request: Request, exc: StorageError) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": str(exc)})

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
