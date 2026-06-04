from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.db.models import Experiment, Run
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentRead,
    ExperimentUpdate,
    LaunchRequest,
    RunRead,
)
from app.services import experiment_service

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentRead, status_code=status.HTTP_201_CREATED)
def create_experiment(body: ExperimentCreate, db: Session = Depends(get_db)) -> Experiment:
    return experiment_service.create_experiment(db, body)


@router.get("", response_model=list[ExperimentRead])
def list_experiments(db: Session = Depends(get_db)) -> list[Experiment]:
    return experiment_service.list_experiments(db)


@router.get("/{experiment_id}", response_model=ExperimentRead)
def get_experiment(experiment_id: int, db: Session = Depends(get_db)) -> Experiment:
    return experiment_service.get_experiment_or_404(db, experiment_id)


@router.put("/{experiment_id}", response_model=ExperimentRead)
def update_experiment(
    experiment_id: int, body: ExperimentUpdate, db: Session = Depends(get_db)
) -> Experiment:
    return experiment_service.update_experiment(db, experiment_id, body)


@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(experiment_id: int, db: Session = Depends(get_db)) -> None:
    experiment_service.delete_experiment(db, experiment_id)


@router.post("/{experiment_id}/launch")
def launch_experiment(
    experiment_id: int,
    body: LaunchRequest = LaunchRequest(),
    db: Session = Depends(get_db),
) -> dict:
    return experiment_service.launch_experiment(db, experiment_id, body.algorithms, body.use_grid)


@router.post("/{experiment_id}/stop")
def stop_experiment(experiment_id: int, db: Session = Depends(get_db)) -> dict:
    return experiment_service.stop_experiment(db, experiment_id)


@router.get("/{experiment_id}/runs", response_model=list[RunRead])
def list_runs(experiment_id: int, db: Session = Depends(get_db)) -> list[Run]:
    return experiment_service.list_runs(db, experiment_id)
