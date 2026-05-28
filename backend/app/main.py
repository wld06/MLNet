from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import cleaning, datasets, deploy, experiments, runs

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


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
