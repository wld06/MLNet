from sqlalchemy.orm import Session

from app.core.exceptions import DatasetNotFoundError
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
