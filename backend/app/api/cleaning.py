from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.cleaning import (
    ApplyPipelineRequest,
    CastColumnRequest,
    DropColumnsRequest,
    DropNullsRequest,
    EncodeRequest,
    FillNullsRequest,
    FilterRowsRequest,
    NormalizeRequest,
    PreviewRequest,
    RenameColumnRequest,
    ReplaceValuesRequest,
    StringOpsRequest,
)
from app.schemas.dataset import DatasetVersionRead
from app.services import cleaning_service

router = APIRouter(prefix="/datasets", tags=["cleaning"])


# ─── Inspection ───────────────────────────────────────────────────────────────

@router.get("/{dataset_id}/quality")
def get_quality(dataset_id: int, db: Session = Depends(get_db)) -> dict:
    return cleaning_service.get_quality(db, dataset_id)


@router.get("/{dataset_id}/columns/{col}/distribution")
def get_distribution(dataset_id: int, col: str, db: Session = Depends(get_db)) -> dict:
    return cleaning_service.get_distribution(db, dataset_id, col)


@router.get("/{dataset_id}/columns/{col}/outliers")
def get_outliers(dataset_id: int, col: str, db: Session = Depends(get_db)) -> dict:
    return cleaning_service.get_outliers(db, dataset_id, col)


@router.get("/{dataset_id}/correlations")
def get_correlations(dataset_id: int, db: Session = Depends(get_db)) -> dict:
    return cleaning_service.get_correlations(db, dataset_id)


@router.get("/{dataset_id}/duplicates")
def get_duplicates(dataset_id: int, db: Session = Depends(get_db)) -> dict:
    return cleaning_service.get_duplicates(db, dataset_id)


# ─── Mutations ────────────────────────────────────────────────────────────────

@router.post("/{dataset_id}/clean/drop-nulls", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def drop_nulls(dataset_id: int, body: DropNullsRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.drop_nulls(db, dataset_id, body.columns, body.how)


@router.post("/{dataset_id}/clean/fill-nulls", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def fill_nulls(dataset_id: int, body: FillNullsRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.fill_nulls(db, dataset_id, body.column, body.strategy, body.value)


@router.post("/{dataset_id}/clean/fill-nulls/bulk", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def fill_nulls_bulk(dataset_id: int, body: list[FillNullsRequest], db: Session = Depends(get_db)) -> DatasetVersionRead:
    ops = [{"column": o.column, "strategy": o.strategy, "value": o.value} for o in body]
    return cleaning_service.fill_nulls_bulk(db, dataset_id, ops)


@router.post("/{dataset_id}/clean/drop-duplicates", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def drop_duplicates(dataset_id: int, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.drop_duplicates(db, dataset_id)


@router.post("/{dataset_id}/clean/cast-column", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def cast_column(dataset_id: int, body: CastColumnRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.cast_column(db, dataset_id, body.column, body.dtype)


@router.post("/{dataset_id}/clean/rename-column", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def rename_column(dataset_id: int, body: RenameColumnRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.rename_column(db, dataset_id, body.old_name, body.new_name)


@router.post("/{dataset_id}/clean/drop-columns", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def drop_columns(dataset_id: int, body: DropColumnsRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.drop_columns(db, dataset_id, body.columns)


@router.post("/{dataset_id}/clean/normalize", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def normalize(dataset_id: int, body: NormalizeRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.normalize(db, dataset_id, body.columns, body.method)


@router.post("/{dataset_id}/clean/encode", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def encode(dataset_id: int, body: EncodeRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.encode(db, dataset_id, body.column, body.method)


@router.post("/{dataset_id}/clean/filter-rows", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def filter_rows(dataset_id: int, body: FilterRowsRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.filter_rows(db, dataset_id, body.column, body.operator, body.value)


@router.post("/{dataset_id}/clean/string-ops", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def string_ops(dataset_id: int, body: StringOpsRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.string_ops(db, dataset_id, body.column, body.operation, body.new_column)


@router.post("/{dataset_id}/clean/replace-values", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def replace_values(dataset_id: int, body: ReplaceValuesRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.replace_values(db, dataset_id, body.column, body.mapping)


# ─── Pipeline ─────────────────────────────────────────────────────────────────

@router.post("/{dataset_id}/clean/preview")
def preview_operation(dataset_id: int, body: PreviewRequest, db: Session = Depends(get_db)) -> dict:
    return cleaning_service.preview_operations(db, dataset_id, body.operations)


@router.post("/{dataset_id}/clean/apply-pipeline", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def apply_pipeline(dataset_id: int, body: ApplyPipelineRequest, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.apply_pipeline(db, dataset_id, body.operations, body.label)


@router.get("/{dataset_id}/clean/history")
def get_history(dataset_id: int, db: Session = Depends(get_db)) -> list:
    return cleaning_service.get_history(db, dataset_id)


@router.post("/{dataset_id}/clean/rollback/{version}", response_model=DatasetVersionRead, status_code=status.HTTP_201_CREATED)
def rollback(dataset_id: int, version: int, db: Session = Depends(get_db)) -> DatasetVersionRead:
    return cleaning_service.rollback(db, dataset_id, version)
