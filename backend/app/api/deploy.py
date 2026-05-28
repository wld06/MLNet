from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.deploy import DeploymentRead, PredictRequest, PredictResponse

router = APIRouter(prefix="/deployments", tags=["deployments"])


@router.get("", response_model=list[DeploymentRead])
async def list_deployments(db: Session = Depends(get_db)) -> list[DeploymentRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{deployment_id}", response_model=DeploymentRead)
async def get_deployment(deployment_id: int, db: Session = Depends(get_db)) -> DeploymentRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deployment(deployment_id: int, db: Session = Depends(get_db)) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{deployment_id}/predict", response_model=PredictResponse)
async def predict(deployment_id: int, body: PredictRequest, db: Session = Depends(get_db)) -> PredictResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{deployment_id}/logs")
async def get_logs(deployment_id: int, db: Session = Depends(get_db)) -> list:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{deployment_id}/rotate-key")
async def rotate_key(deployment_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{deployment_id}/export/docker")
async def export_docker(deployment_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{deployment_id}/export/notebook")
async def export_notebook(deployment_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
