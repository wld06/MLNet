import json
import secrets
import textwrap
from datetime import datetime

import mlflow.sklearn
import pandas as pd
from sqlalchemy.orm import Session

from app.core.exceptions import DeploymentNotFoundError, RunNotFoundError
from app.db.models import DeployedModel, Run
from app.schemas.deploy import PredictRequest


def get_deployment_or_404(db: Session, deployment_id: int) -> DeployedModel:
    dep = db.get(DeployedModel, deployment_id)
    if not dep:
        raise DeploymentNotFoundError(f"Deployment {deployment_id} not found")
    return dep


def list_deployments(db: Session) -> list[DeployedModel]:
    return db.query(DeployedModel).all()


def deploy_run(db: Session, run_id: int, name: str) -> DeployedModel:
    run = db.get(Run, run_id)
    if not run:
        raise RunNotFoundError(f"Run {run_id} not found")
    if run.status != "completed" or not run.model_path:
        raise ValueError(f"Run {run_id} is not completed or has no model")
    api_key = secrets.token_urlsafe(32)
    dep = DeployedModel(
        run_id=run_id,
        name=name,
        endpoint_url="",
        api_key=api_key,
        status="active",
    )
    db.add(dep)
    db.flush()
    dep.endpoint_url = f"/api/deployments/{dep.id}/predict"
    db.commit()
    db.refresh(dep)
    return dep


def delete_deployment(db: Session, deployment_id: int) -> None:
    dep = get_deployment_or_404(db, deployment_id)
    dep.status = "inactive"
    db.commit()


def predict(db: Session, deployment_id: int, body: PredictRequest) -> dict:
    dep = get_deployment_or_404(db, deployment_id)
    if dep.status != "active":
        raise ValueError("Deployment is not active")
    run = db.get(Run, dep.run_id)
    pipeline = mlflow.sklearn.load_model(run.model_path)
    X = pd.DataFrame([body.features])
    raw_prediction = pipeline.predict(X)[0]
    prediction = raw_prediction.item() if hasattr(raw_prediction, "item") else raw_prediction
    probabilities = None
    if hasattr(pipeline, "predict_proba"):
        try:
            proba = pipeline.predict_proba(X)[0]
            classes = [str(c) for c in pipeline.classes_]
            probabilities = dict(zip(classes, proba.tolist()))
        except Exception:
            pass
    dep.request_count = (dep.request_count or 0) + 1
    dep.last_called_at = datetime.utcnow()
    db.commit()
    return {"prediction": prediction, "probabilities": probabilities}


def rotate_api_key(db: Session, deployment_id: int) -> dict:
    dep = get_deployment_or_404(db, deployment_id)
    dep.api_key = secrets.token_urlsafe(32)
    db.commit()
    return {"api_key": dep.api_key}


def export_docker(db: Session, deployment_id: int) -> dict:
    dep = get_deployment_or_404(db, deployment_id)
    run = db.get(Run, dep.run_id)
    content = textwrap.dedent(f"""
        version: "3.9"
        services:
          predictor:
            image: python:3.11-slim
            environment:
              MODEL_PATH: "{run.model_path}"
              API_KEY: "{dep.api_key}"
            ports:
              - "8080:8080"
            command: >
              bash -c "pip install fastapi uvicorn mlflow scikit-learn pandas &&
                       uvicorn predictor:app --host 0.0.0.0 --port 8080"
    """).strip()
    return {"filename": "docker-compose.yml", "content": content}


def export_notebook(db: Session, deployment_id: int) -> dict:
    dep = get_deployment_or_404(db, deployment_id)
    run = db.get(Run, dep.run_id)
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": f"# Deployment: {dep.name}",
            },
            {
                "cell_type": "code",
                "metadata": {},
                "outputs": [],
                "source": (
                    "import mlflow.sklearn\nimport pandas as pd\n\n"
                    f'pipeline = mlflow.sklearn.load_model("{run.model_path}")\n\n'
                    "# Replace with your actual feature values\n"
                    'X = pd.DataFrame([{"feature1": 0, "feature2": 1}])\n'
                    "prediction = pipeline.predict(X)\n"
                    "print(prediction)"
                ),
            },
        ],
    }
    return {"filename": f"{dep.name}.ipynb", "content": json.dumps(nb, indent=2)}
