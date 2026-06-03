from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.db.models import Dataset, DatasetVersion
from app.schemas.dataset import DatasetPreviewResponse, DatasetRead, DatasetVersionRead
from app.services import dataset_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload", response_model=DatasetRead, status_code=status.HTTP_201_CREATED)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)) -> Dataset:
    return await dataset_service.create_dataset(db, file)


@router.get("", response_model=list[DatasetRead])
def list_datasets(db: Session = Depends(get_db)) -> list[Dataset]:
    return dataset_service.list_datasets(db)


@router.get("/{dataset_id}", response_model=DatasetRead)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)) -> Dataset:
    return dataset_service.get_dataset_or_404(db, dataset_id)


@router.get("/{dataset_id}/preview", response_model=DatasetPreviewResponse)
def get_dataset_preview(
    dataset_id: int,
    rows: int = Query(default=50, le=500),
    db: Session = Depends(get_db),
) -> DatasetPreviewResponse:
    result = dataset_service.get_preview(db, dataset_id, rows)
    return DatasetPreviewResponse(**result)


@router.get("/{dataset_id}/profile")
def get_dataset_profile(dataset_id: int, db: Session = Depends(get_db)) -> dict:
    return dataset_service.get_profile(db, dataset_id)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(dataset_id: int, db: Session = Depends(get_db)) -> None:
    dataset_service.delete_dataset(db, dataset_id)


@router.get("/{dataset_id}/versions", response_model=list[DatasetVersionRead])
def list_versions(dataset_id: int, db: Session = Depends(get_db)) -> list[DatasetVersion]:
    return dataset_service.list_versions(db, dataset_id)


@router.get("/{dataset_id}/versions/{version}", response_model=DatasetVersionRead)
def get_version(dataset_id: int, version: int, db: Session = Depends(get_db)) -> DatasetVersion:
    return dataset_service.get_version_or_404(db, dataset_id, version)


@router.post("/{dataset_id}/versions/{version}/export")
def export_version(dataset_id: int, version: int, db: Session = Depends(get_db)) -> dict:
    return dataset_service.export_version(db, dataset_id, version)