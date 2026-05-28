from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.experiment import ExperimentCreate, ExperimentRead, ExperimentUpdate, RunRead

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
async def create_experiment(body: ExperimentCreate, db: Session = Depends(get_db)) -> ExperimentRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("", response_model=list[ExperimentRead])
async def list_experiments(db: Session = Depends(get_db)) -> list[ExperimentRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{experiment_id}", response_model=ExperimentRead)
async def get_experiment(experiment_id: int, db: Session = Depends(get_db)) -> ExperimentRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.put("/{experiment_id}", response_model=ExperimentRead)
async def update_experiment(experiment_id: int, body: ExperimentUpdate, db: Session = Depends(get_db)) -> ExperimentRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_experiment(experiment_id: int, db: Session = Depends(get_db)) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{experiment_id}/launch")
async def launch_experiment(experiment_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{experiment_id}/stop")
async def stop_experiment(experiment_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{experiment_id}/runs", response_model=list[RunRead])
async def list_runs(experiment_id: int, db: Session = Depends(get_db)) -> list[RunRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
