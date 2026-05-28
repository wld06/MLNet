from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.experiment import RunRead

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("/{run_id}", response_model=RunRead)
async def get_run(run_id: int, db: Session = Depends(get_db)) -> RunRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{run_id}/metrics")
async def get_metrics(run_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{run_id}/shap")
async def get_shap(run_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{run_id}/feature-importance")
async def get_feature_importance(run_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{run_id}/confusion-matrix")
async def get_confusion_matrix(run_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{run_id}/learning-curve")
async def get_learning_curve(run_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{run_id}/deploy")
async def deploy_run(run_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
