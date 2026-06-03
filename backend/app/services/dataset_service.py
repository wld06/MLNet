import uuid
from io import BytesIO

import numpy as np
import pandas as pd
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import DatasetNotFoundError, DatasetTooLargeError
from app.core.storage import delete_file, download_file, get_presigned_url, upload_file
from app.db.models import Dataset, DatasetVersion

def get_dataset_or_404(db: Session, dataset_id: int) -> Dataset:
    dataset = db.get(Dataset, dataset_id)
    if not dataset:
        raise DatasetNotFoundError(f"Dataset {dataset_id} not found")
    return dataset


def get_version_or_404(db: Session, dataset_id: int, version_number: int) -> DatasetVersion:
    version = (
        db.query(DatasetVersion)
        .filter(
            DatasetVersion.dataset_id == dataset_id,
            DatasetVersion.version_number == version_number,
        )
        .first()
    )
    if not version:
        raise DatasetNotFoundError(f"Dataset {dataset_id} version {version_number} not found")
    return version


async def create_dataset(db: Session, file: UploadFile) -> Dataset:
    contents = await file.read()

    max_bytes = settings.MAX_DATASET_SIZE_MB * 1024 * 1024
    
    if len(contents) > max_bytes:
        raise DatasetTooLargeError(f"File exceeds {settings.MAX_DATASET_SIZE_MB}MB limit")
    
    df = pd.read_csv(BytesIO(contents))

    column_metadata = {col: str(dtype) for col, dtype in df.dtypes.items()}

    key = f"datasets/{uuid.uuid4()}/{file.filename}"
    upload_file(BytesIO(contents), key)

    dataset = Dataset(
        name=file.filename.rsplit(".", 1)[0],
        filename=file.filename,
        storage_path=key,
        size_bytes=len(contents),
        row_count=len(df),
        col_count=len(df.columns),
        column_metadata=column_metadata,
    )
    db.add(dataset)
    db.flush()

    version = DatasetVersion(
        dataset_id=dataset.id,
        version_number=0,
        storage_path=key,
        row_count=len(df),
        col_count=len(df.columns),
        operations_log=[],
        label="raw",
    )
    db.add(version)
    db.commit()
    db.refresh(dataset)

    return dataset

def get_preview(db: Session, dataset_id: int, rows: int) -> dict:
    dataset = get_dataset_or_404(db, dataset_id)
    buf = download_file(dataset.storage_path)
    df = pd.read_csv(buf, nrows=rows)
    return {
        "columns": df.columns.to_list(),
        "rows": df.values.tolist(),
        "total_rows": dataset.row_count or 0,
    }


def delete_dataset(db: Session, dataset_id: int) -> None:
    dataset = get_dataset_or_404(db, dataset_id)
    delete_file(dataset.storage_path)
    db.delete(dataset)
    db.commit()

def list_datasets(db: Session) -> list[Dataset]:
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()

def list_versions(db: Session, dataset_id: int) -> list[DatasetVersion]:
    get_dataset_or_404(db, dataset_id)

    return (
        db.query(DatasetVersion)
        .filter(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.version_number)
        .all()
    )

def get_profile(db: Session, dataset_id: int) -> dict:
    dataset = get_dataset_or_404(db, dataset_id)

    if dataset.profile:
        return dataset.profile
    
    buf = download_file(dataset.storage_path)
    df = pd.read_csv(buf)

    columns = {}

    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        info: dict = {
            "dtype": str(series.dtype),
            "null_count": null_count,
            "null_pct": round(null_count / len(df) * 100, 2) if len(df) else 0,
            "unique_count": int(series.nunique()),
        }
    
        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            info["min"] = _safe_float(desc.get("min"))
            info["max"] = _safe_float(desc.get("max"))
            info["mean"] = _safe_float(desc.get("mean"))
            info["std"] = _safe_float(desc.get("std"))
            info["p25"] = _safe_float(desc.get("25%"))
            info["p50"] = _safe_float(desc.get("50%"))
            info["p75"] = _safe_float(desc.get("75%"))
        else:
            top = series.dropna().value_counts().head(5)
            info["top_values"] = top.index.to_list()
            
        columns[col] = info

    profile = {
        "row_count": len(df),
        "col_count": len(df.columns),
        "columns": columns,
    }

    dataset.profile = profile
    db.commit()

    return profile


def _safe_float(val) -> float | None:
    if val is None:
        return None
    
    try:
        f = float(val)
        return None if  np.isnan(f) or np.isinf(f) else round(f, 6)
    except (TypeError, ValueError):
        return None

def export_version(db: Session, dataset_id: int, version_number: int) -> dict:
    version = get_version_or_404(db, dataset_id, version_number)
    url = get_presigned_url(version.storage_path, expires_in=3600)
    return {"download_url": url, "expires_in": 3600}