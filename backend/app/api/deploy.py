from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.exceptions import DeploymentNotFoundError
from app.schemas.deploy import DeploymentRead, PredictRequest, PredictResponse
from app.services import deploy_service

router = APIRouter(prefix="/deployments", tags=["deployments"])


def _not_found(exc: Exception):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("", response_model=list[DeploymentRead])
def list_deployments(db: Session = Depends(get_db)) -> list[DeploymentRead]:
    return deploy_service.list_deployments(db)


@router.get("/{deployment_id}", response_model=DeploymentRead)
def get_deployment(deployment_id: int, db: Session = Depends(get_db)) -> DeploymentRead:
    try:
        return deploy_service.get_deployment_or_404(db, deployment_id)
    except DeploymentNotFoundError as e:
        _not_found(e)


@router.delete("/{deployment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_deployment(deployment_id: int, db: Session = Depends(get_db)) -> None:
    try:
        deploy_service.delete_deployment(db, deployment_id)
    except DeploymentNotFoundError as e:
        _not_found(e)


@router.post("/{deployment_id}/predict", response_model=PredictResponse)
def predict(deployment_id: int, body: PredictRequest, db: Session = Depends(get_db)) -> PredictResponse:
    try:
        result = deploy_service.predict(db, deployment_id, body)
        return PredictResponse(**result)
    except DeploymentNotFoundError as e:
        _not_found(e)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{deployment_id}/logs")
def get_logs(deployment_id: int, db: Session = Depends(get_db)) -> list:
    try:
        dep = deploy_service.get_deployment_or_404(db, deployment_id)
        return [
            {
                "deployment_id": dep.id,
                "request_count": dep.request_count,
                "last_called_at": dep.last_called_at.isoformat() if dep.last_called_at else None,
                "status": dep.status,
            }
        ]
    except DeploymentNotFoundError as e:
        _not_found(e)


@router.post("/{deployment_id}/rotate-key")
def rotate_key(deployment_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return deploy_service.rotate_api_key(db, deployment_id)
    except DeploymentNotFoundError as e:
        _not_found(e)


@router.get("/{deployment_id}/export/docker")
def export_docker(deployment_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return deploy_service.export_docker(db, deployment_id)
    except DeploymentNotFoundError as e:
        _not_found(e)


@router.get("/{deployment_id}/export/notebook")
def export_notebook(deployment_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return deploy_service.export_notebook(db, deployment_id)
    except DeploymentNotFoundError as e:
        _not_found(e)
