from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer)
    col_count: Mapped[int | None] = mapped_column(Integer)
    column_metadata: Mapped[dict | None] = mapped_column(JSON)
    profile: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int | None] = mapped_column(Integer)

    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="dataset")
    cleaning_operations: Mapped[list["CleaningOperation"]] = relationship(back_populates="dataset")


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer)
    col_count: Mapped[int | None] = mapped_column(Integer)
    operations_log: Mapped[list | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    label: Mapped[str | None] = mapped_column(String(255))

    dataset: Mapped["Dataset"] = relationship(back_populates="versions")


class CleaningOperation(Base):
    __tablename__ = "cleaning_operations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    operation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    parameters: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    rows_affected: Mapped[int | None] = mapped_column(Integer)
    preview_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dataset: Mapped["Dataset"] = relationship(back_populates="cleaning_operations")


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_version_id: Mapped[int] = mapped_column(ForeignKey("dataset_versions.id"), nullable=False)
    target_column: Mapped[str] = mapped_column(String(255), nullable=False)
    feature_columns: Mapped[list | None] = mapped_column(JSON)
    problem_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user_id: Mapped[int | None] = mapped_column(Integer)

    runs: Mapped[list["Run"]] = relationship(back_populates="experiment")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    experiment_id: Mapped[int] = mapped_column(ForeignKey("experiments.id"), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    hyperparameters: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    metrics: Mapped[dict | None] = mapped_column(JSON)
    mlflow_run_id: Mapped[str | None] = mapped_column(String(255))
    model_path: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)

    experiment: Mapped["Experiment"] = relationship(back_populates="runs")
    deployment: Mapped["DeployedModel | None"] = relationship(back_populates="run")


class DeployedModel(Base):
    __tablename__ = "deployed_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    endpoint_url: Mapped[str | None] = mapped_column(Text)
    api_key: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    request_count: Mapped[int] = mapped_column(Integer, default=0)
    last_called_at: Mapped[datetime | None] = mapped_column(DateTime)

    run: Mapped["Run"] = relationship(back_populates="deployment")
