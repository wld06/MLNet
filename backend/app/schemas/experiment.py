from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExperimentCreate(BaseModel):
    name: str
    dataset_version_id: int
    target_column: str
    feature_columns: list[str]
    problem_type: str  # classification | regression


class ExperimentUpdate(BaseModel):
    name: str | None = None
    feature_columns: list[str] | None = None


class LaunchRequest(BaseModel):
    algorithms: list[str] | None = None  # None = all for problem_type
    use_grid: bool = False  # True = expand param_grid into one run per combo


class ExperimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    dataset_version_id: int
    target_column: str
    feature_columns: list | None
    problem_type: str
    status: str
    created_at: datetime


class RunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_id: int
    algorithm: str
    hyperparameters: dict | None
    status: str
    metrics: dict | None
    mlflow_run_id: str | None
    model_path: str | None
    started_at: datetime | None
    finished_at: datetime | None
