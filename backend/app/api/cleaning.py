from fastapi import APIRouter, Depends, HTTPException, status
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

router = APIRouter(prefix="/datasets", tags=["cleaning"])


@router.get("/{dataset_id}/quality")
async def get_quality(dataset_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}/columns/{col}/distribution")
async def get_distribution(dataset_id: int, col: str, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}/columns/{col}/outliers")
async def get_outliers(dataset_id: int, col: str, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}/correlations")
async def get_correlations(dataset_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}/duplicates")
async def get_duplicates(dataset_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/drop-nulls")
async def drop_nulls(dataset_id: int, body: DropNullsRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/fill-nulls")
async def fill_nulls(dataset_id: int, body: FillNullsRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/fill-nulls/bulk")
async def fill_nulls_bulk(dataset_id: int, body: list[FillNullsRequest], db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/drop-duplicates")
async def drop_duplicates(dataset_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/cast-column")
async def cast_column(dataset_id: int, body: CastColumnRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/rename-column")
async def rename_column(dataset_id: int, body: RenameColumnRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/drop-columns")
async def drop_columns(dataset_id: int, body: DropColumnsRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/normalize")
async def normalize(dataset_id: int, body: NormalizeRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/encode")
async def encode(dataset_id: int, body: EncodeRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/filter-rows")
async def filter_rows(dataset_id: int, body: FilterRowsRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/string-ops")
async def string_ops(dataset_id: int, body: StringOpsRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/replace-values")
async def replace_values(dataset_id: int, body: ReplaceValuesRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/preview")
async def preview_operation(dataset_id: int, body: PreviewRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/apply-pipeline")
async def apply_pipeline(dataset_id: int, body: ApplyPipelineRequest, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}/clean/history")
async def get_history(dataset_id: int, db: Session = Depends(get_db)) -> list:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/clean/rollback/{version}")
async def rollback(dataset_id: int, version: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
