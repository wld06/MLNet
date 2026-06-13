from app.core.events import cleaning_channel, publish
from app.db.session import SessionLocal
from app.services import cleaning_service
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="cleaning.apply_pipeline")
def apply_pipeline_task(
    self, dataset_id: int, operations: list[dict], label: str | None = None
) -> dict:
    """Apply a cleaning pipeline in the background, streaming progress over WS."""
    channel = cleaning_channel(dataset_id)
    db = SessionLocal()

    def emit(payload: dict) -> None:
        try:
            publish(channel, payload)
        except Exception:
            pass

    emit({"event": "pipeline_started", "dataset_id": dataset_id, "total": len(operations)})

    def on_progress(idx: int, total: int, operation: str) -> None:
        emit({
            "event": "operation_done",
            "dataset_id": dataset_id,
            "step": idx,
            "total": total,
            "operation": operation,
        })

    try:
        version = cleaning_service.apply_pipeline(
            db, dataset_id, operations, label, on_progress=on_progress
        )
    except Exception as exc:
        emit({"event": "pipeline_failed", "dataset_id": dataset_id, "error": str(exc)})
        raise
    finally:
        db.close()

    result = {
        "dataset_id": dataset_id,
        "version": version.version_number,
        "row_count": version.row_count,
        "col_count": version.col_count,
    }
    emit({"event": "pipeline_completed", **result})
    return result
