from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    name: str
    filename: str


class DatasetCreate(DatasetBase):
    storage_path: str
    size_bytes: int


class DatasetRead(DatasetBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    size_bytes: int
    row_count: int | None
    col_count: int | None
    column_metadata: dict | None
    created_at: datetime


class DatasetPreviewResponse(BaseModel):
    columns: list[str]
    rows: list[list]
    total_rows: int


class DatasetVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dataset_id: int
    version_number: int
    row_count: int | None
    col_count: int | None
    operations_log: list | None
    created_at: datetime
    label: str | None
