import numpy as np
import pandas as pd
import mlflow.sklearn
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import learning_curve
from sqlalchemy.orm import Session

from app.core.exceptions import DatasetVersionNotFoundError, RunNotFoundError
from app.core.storage import download_file
from app.db.models import DatasetVersion, Experiment, Run
from app.ml.explainability import compute_shap_values


def _load_run_and_data(db: Session, run_id: int) -> tuple:
    run = db.get(Run, run_id)
    if not run:
        raise RunNotFoundError(f"Run {run_id} not found")
    experiment = db.get(Experiment, run.experiment_id)
    version = db.get(DatasetVersion, experiment.dataset_version_id)
    if not version:
        raise DatasetVersionNotFoundError(f"DatasetVersion not found")
    df = pd.read_csv(download_file(version.storage_path))
    features = experiment.feature_columns or [c for c in df.columns if c != experiment.target_column]
    X = df[features]
    y = df[experiment.target_column]
    return run, experiment, X, y


def get_run_metrics(db: Session, run_id: int) -> dict:
    run = db.get(Run, run_id)
    if not run:
        raise RunNotFoundError(f"Run {run_id} not found")
    return run.metrics or {}


def get_shap_values(db: Session, run_id: int) -> dict:
    run, experiment, X, y = _load_run_and_data(db, run_id)
    if not run.model_path:
        raise RunNotFoundError(f"Run {run_id} has no trained model")
    pipeline = mlflow.sklearn.load_model(run.model_path)
    sample = X.sample(min(200, len(X)), random_state=42)
    return compute_shap_values(pipeline, sample)


def get_feature_importance(db: Session, run_id: int) -> dict:
    run, experiment, X, y = _load_run_and_data(db, run_id)
    if not run.model_path:
        raise RunNotFoundError(f"Run {run_id} has no trained model")
    pipeline = mlflow.sklearn.load_model(run.model_path)
    estimator = pipeline.steps[-1][1]
    if hasattr(estimator, "feature_importances_"):
        features = experiment.feature_columns or list(X.columns)
        importances = estimator.feature_importances_.tolist()
        return {"feature_importance": dict(zip(features, importances)), "source": "model"}
    sample = X.sample(min(200, len(X)), random_state=42)
    shap_data = compute_shap_values(pipeline, sample)
    return {"feature_importance": shap_data["feature_importance"], "source": "shap"}


def get_confusion_matrix(db: Session, run_id: int) -> dict:
    run, experiment, X, y = _load_run_and_data(db, run_id)
    if experiment.problem_type != "classification":
        raise ValueError("Confusion matrix only available for classification")
    if not run.model_path:
        raise RunNotFoundError(f"Run {run_id} has no trained model")
    pipeline = mlflow.sklearn.load_model(run.model_path)
    y_pred = pipeline.predict(X)
    labels = sorted(y.unique().tolist())
    matrix = confusion_matrix(y, y_pred, labels=labels).tolist()
    return {"labels": [str(l) for l in labels], "matrix": matrix}


def get_learning_curve(db: Session, run_id: int) -> dict:
    run, experiment, X, y = _load_run_and_data(db, run_id)
    if not run.model_path:
        raise RunNotFoundError(f"Run {run_id} has no trained model")
    pipeline = mlflow.sklearn.load_model(run.model_path)
    scoring = "accuracy" if experiment.problem_type == "classification" else "r2"
    train_sizes, train_scores, val_scores = learning_curve(
        pipeline, X, y, cv=5, n_jobs=-1,
        train_sizes=np.linspace(0.1, 1.0, 8),
        scoring=scoring,
    )
    return {
        "train_sizes": train_sizes.tolist(),
        "train_scores_mean": train_scores.mean(axis=1).tolist(),
        "train_scores_std": train_scores.std(axis=1).tolist(),
        "val_scores_mean": val_scores.mean(axis=1).tolist(),
        "val_scores_std": val_scores.std(axis=1).tolist(),
    }
