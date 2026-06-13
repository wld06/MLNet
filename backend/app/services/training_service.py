from datetime import datetime

import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.model_selection import cross_val_predict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.events import experiment_channel, publish
from app.core.exceptions import (
    DatasetVersionNotFoundError,
    ExperimentNotFoundError,
    RunNotFoundError,
)
from app.core.storage import download_file
from app.db.models import DatasetVersion, Experiment, Run
from app.ml.algorithms import get_algorithm
from app.ml.metrics import compute_classification_metrics, compute_regression_metrics
from app.ml.pipeline import build_pipeline, build_preprocessor

CV_FOLDS = 5


def train_run(db: Session, experiment_id: int, run_id: int) -> dict:
    """Train a single run end-to-end and persist its results."""
    run = db.get(Run, run_id)
    if not run:
        raise RunNotFoundError(f"Run {run_id} not found")
    experiment = db.get(Experiment, experiment_id)
    if not experiment:
        raise ExperimentNotFoundError(f"Experiment {experiment_id} not found")

    run.status = "running"
    run.started_at = datetime.utcnow()
    db.commit()
    _emit(experiment.id, "run_started", run_id=run.id, algorithm=run.algorithm)

    try:
        result = _execute_training(db, experiment, run)
    except Exception as exc:
        run.status = "failed"
        run.metrics = {"error": str(exc)}
        run.finished_at = datetime.utcnow()
        db.commit()
        _emit(experiment.id, "run_failed", run_id=run.id, error=str(exc))
        _finalize_experiment(db, experiment)
        raise

    run.metrics = result["metrics"]
    run.model_path = result["model_path"]
    run.mlflow_run_id = result["mlflow_run_id"]
    run.status = "completed"
    run.finished_at = datetime.utcnow()
    db.commit()
    _emit(experiment.id, "run_completed", run_id=run.id, metrics=run.metrics)

    _finalize_experiment(db, experiment)
    return {"run_id": run.id, "status": run.status, "metrics": run.metrics}


def _emit(experiment_id: int, event: str, **data) -> None:
    """Publish a training progress event. Never let pub/sub failures break a run."""
    try:
        publish(experiment_channel(experiment_id), {"event": event, **data})
    except Exception:
        pass


def _execute_training(db: Session, experiment: Experiment, run: Run) -> dict:
    version = db.get(DatasetVersion, experiment.dataset_version_id)
    if not version:
        raise DatasetVersionNotFoundError(
            f"Dataset version {experiment.dataset_version_id} not found"
        )

    df = pd.read_csv(download_file(version.storage_path))

    features = experiment.feature_columns or [
        c for c in df.columns if c != experiment.target_column
    ]
    X = df[features]
    y = df[experiment.target_column]

    cfg = get_algorithm(run.algorithm)
    estimator = cfg.estimator_class(**(run.hyperparameters or {}))
    pipeline = build_pipeline(estimator, build_preprocessor(X))

    n_splits = max(2, min(CV_FOLDS, len(y)))
    metrics = _cross_validate(pipeline, X, y, experiment.problem_type, n_splits)

    pipeline.fit(X, y)

    mlflow.set_tracking_uri(settings.MLFLOW_TRACKING_URI)
    mlflow.set_experiment(experiment.name)
    with mlflow.start_run(run_name=f"{run.algorithm}-{run.id}") as ml_run:
        mlflow.log_param("algorithm", run.algorithm)
        mlflow.log_params(run.hyperparameters or {})
        mlflow.log_metrics(metrics)
        mlflow.sklearn.log_model(pipeline, artifact_path="model")
        mlflow_run_id = ml_run.info.run_id

    return {
        "metrics": metrics,
        "model_path": f"runs:/{mlflow_run_id}/model",
        "mlflow_run_id": mlflow_run_id,
    }


def _cross_validate(pipeline, X, y, problem_type: str, n_splits: int) -> dict:
    y_pred = cross_val_predict(pipeline, X, y, cv=n_splits)

    if problem_type == "classification":
        y_proba = None
        if hasattr(pipeline, "predict_proba"):
            try:
                y_proba = cross_val_predict(
                    pipeline, X, y, cv=n_splits, method="predict_proba"
                )
            except (ValueError, AttributeError):
                y_proba = None
        metrics = compute_classification_metrics(y, y_pred, y_proba)
    else:
        metrics = compute_regression_metrics(y, y_pred)

    return {k: float(v) for k, v in metrics.items()}


def _finalize_experiment(db: Session, experiment: Experiment) -> None:
    remaining = (
        db.query(Run)
        .filter(
            Run.experiment_id == experiment.id,
            Run.status.in_(["pending", "running"]),
        )
        .count()
    )
    if remaining == 0 and experiment.status == "running":
        experiment.status = "completed"
        db.commit()
        _emit(experiment.id, "experiment_completed", experiment_id=experiment.id)
