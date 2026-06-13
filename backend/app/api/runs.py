from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.core.exceptions import RunNotFoundError
from app.db.models import Run
from app.schemas.deploy import DeployRequest, DeploymentRead
from app.schemas.experiment import RunRead
from app.services import deploy_service, metrics_service

router = APIRouter(prefix="/runs", tags=["runs"])


def _not_found(exc: Exception):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{run_id}", response_model=RunRead)
def get_run(run_id: int, db: Session = Depends(get_db)) -> Run:
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run {run_id} not found")
    return run


@router.get("/{run_id}/metrics")
def get_metrics(run_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return metrics_service.get_run_metrics(db, run_id)
    except RunNotFoundError as e:
        _not_found(e)


@router.get("/{run_id}/shap")
def get_shap(run_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return metrics_service.get_shap_values(db, run_id)
    except RunNotFoundError as e:
        _not_found(e)


@router.get("/{run_id}/feature-importance")
def get_feature_importance(run_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return metrics_service.get_feature_importance(db, run_id)
    except RunNotFoundError as e:
        _not_found(e)


@router.get("/{run_id}/confusion-matrix")
def get_confusion_matrix(run_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return metrics_service.get_confusion_matrix(db, run_id)
    except RunNotFoundError as e:
        _not_found(e)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{run_id}/learning-curve")
def get_learning_curve(run_id: int, db: Session = Depends(get_db)) -> dict:
    try:
        return metrics_service.get_learning_curve(db, run_id)
    except RunNotFoundError as e:
        _not_found(e)


@router.post("/{run_id}/deploy", response_model=DeploymentRead, status_code=status.HTTP_201_CREATED)
def deploy_run(run_id: int, body: DeployRequest, db: Session = Depends(get_db)) -> DeploymentRead:
    try:
        return deploy_service.deploy_run(db, run_id, body.name)
    except RunNotFoundError as e:
        _not_found(e)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
