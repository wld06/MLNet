import itertools

from sqlalchemy.orm import Session

from app.core.exceptions import (
    DatasetVersionNotFoundError,
    ExperimentNotFoundError,
    InvalidOperationError,
)
from app.db.models import DatasetVersion, Experiment, Run
from app.ml.algorithms import get_algorithm, get_algorithms_for_problem
from app.schemas.experiment import ExperimentCreate, ExperimentUpdate

VALID_PROBLEM_TYPES = {"classification", "regression"}


def get_experiment_or_404(db: Session, experiment_id: int) -> Experiment:
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise ExperimentNotFoundError(f"Experiment {experiment_id} not found")
    return experiment


def create_experiment(db: Session, body: ExperimentCreate) -> Experiment:
    if body.problem_type not in VALID_PROBLEM_TYPES:
        raise InvalidOperationError(
            f"Invalid problem_type '{body.problem_type}'. Valid: {sorted(VALID_PROBLEM_TYPES)}"
        )

    version = db.get(DatasetVersion, body.dataset_version_id)
    if not version:
        raise DatasetVersionNotFoundError(
            f"Dataset version {body.dataset_version_id} not found"
        )

    experiment = Experiment(
        name=body.name,
        dataset_version_id=body.dataset_version_id,
        target_column=body.target_column,
        feature_columns=body.feature_columns,
        problem_type=body.problem_type,
        status="pending",
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment


def list_experiments(db: Session) -> list[Experiment]:
    return db.query(Experiment).order_by(Experiment.created_at.desc()).all()


def update_experiment(db: Session, experiment_id: int, body: ExperimentUpdate) -> Experiment:
    experiment = get_experiment_or_404(db, experiment_id)

    if experiment.status == "running":
        raise InvalidOperationError("Cannot update a running experiment")

    if body.name is not None:
        experiment.name = body.name
    if body.feature_columns is not None:
        experiment.feature_columns = body.feature_columns

    db.commit()
    db.refresh(experiment)
    return experiment


def delete_experiment(db: Session, experiment_id: int) -> None:
    experiment = get_experiment_or_404(db, experiment_id)
    if experiment.status == "running":
        raise InvalidOperationError("Cannot delete a running experiment")
    db.delete(experiment)
    db.commit()


def list_runs(db: Session, experiment_id: int) -> list[Run]:
    get_experiment_or_404(db, experiment_id)
    return (
        db.query(Run)
        .filter(Run.experiment_id == experiment_id)
        .order_by(Run.id)
        .all()
    )


def _expand_param_grid(param_grid: dict) -> list[dict]:
    if not param_grid:
        return [{}]
    keys = list(param_grid)
    combos = itertools.product(*(param_grid[k] for k in keys))
    return [dict(zip(keys, values, strict=True)) for values in combos]


def _build_run_specs(problem_type: str, algorithms: list[str] | None, use_grid: bool) -> list[dict]:
    if algorithms:
        configs = {key: get_algorithm(key) for key in algorithms}
        for key, cfg in configs.items():
            if cfg.problem_type != problem_type:
                raise InvalidOperationError(
                    f"Algorithm '{key}' is {cfg.problem_type}, "
                    f"experiment is {problem_type}"
                )
    else:
        configs = get_algorithms_for_problem(problem_type)

    specs: list[dict] = []
    for key, cfg in configs.items():
        if use_grid:
            for params in _expand_param_grid(cfg.param_grid):
                specs.append({"algorithm": key, "hyperparameters": {**cfg.default_params, **params}})
        else:
            specs.append({"algorithm": key, "hyperparameters": dict(cfg.default_params)})
    return specs


def launch_experiment(
    db: Session, experiment_id: int, algorithms: list[str] | None, use_grid: bool
) -> dict:
    experiment = get_experiment_or_404(db, experiment_id)

    if experiment.status == "running":
        raise InvalidOperationError("Experiment is already running")

    specs = _build_run_specs(experiment.problem_type, algorithms, use_grid)
    if not specs:
        raise InvalidOperationError("No algorithms to run")

    runs: list[Run] = []
    for spec in specs:
        run = Run(
            experiment_id=experiment.id,
            algorithm=spec["algorithm"],
            hyperparameters=spec["hyperparameters"],
            status="pending",
        )
        db.add(run)
        runs.append(run)

    experiment.status = "running"
    db.commit()
    for run in runs:
        db.refresh(run)

    # Import here to avoid pulling Celery into request path at module load
    from app.workers.training_tasks import run_experiment_task

    for run in runs:
        run_experiment_task.delay(experiment.id, run.id)

    return {
        "experiment_id": experiment.id,
        "status": experiment.status,
        "runs_queued": len(runs),
        "run_ids": [r.id for r in runs],
    }


def stop_experiment(db: Session, experiment_id: int) -> dict:
    experiment = get_experiment_or_404(db, experiment_id)

    if experiment.status != "running":
        raise InvalidOperationError("Experiment is not running")

    pending = (
        db.query(Run)
        .filter(Run.experiment_id == experiment_id, Run.status.in_(["pending", "running"]))
        .all()
    )
    for run in pending:
        run.status = "failed"

    experiment.status = "stopped"
    db.commit()

    return {
        "experiment_id": experiment.id,
        "status": experiment.status,
        "runs_cancelled": len(pending),
    }
