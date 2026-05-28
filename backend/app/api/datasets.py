from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.dataset import DatasetPreviewResponse, DatasetRead, DatasetVersionRead

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
async def upload_dataset(file: UploadFile, db: Session = Depends(get_db)) -> DatasetRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("", response_model=list[DatasetRead])
async def list_datasets(db: Session = Depends(get_db)) -> list[DatasetRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}", response_model=DatasetRead)
async def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> DatasetRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
async def get_dataset_preview(
    dataset_id: int,
    rows: int = Query(default=50, le=500),
    db: Session = Depends(get_db),
) -> DatasetPreviewResponse:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}/profile")
async def get_dataset_profile(dataset_id: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: int, db: Session = Depends(get_db)) -> None:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionRead])
async def list_versions(dataset_id: int, db: Session = Depends(get_db)) -> list[DatasetVersionRead]:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.get("/{dataset_id}/versions/{version}", response_model=DatasetVersionRead)
async def get_version(dataset_id: int, version: int, db: Session = Depends(get_db)) -> DatasetVersionRead:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)


@router.post("/{dataset_id}/versions/{version}/export")
async def export_version(dataset_id: int, version: int, db: Session = Depends(get_db)) -> dict:
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED)
