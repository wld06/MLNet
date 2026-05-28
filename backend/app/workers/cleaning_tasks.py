from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="cleaning.apply_pipeline")
def apply_pipeline_task(self, dataset_id: int, operations: list[dict], label: str | None = None) -> dict:
    # TODO: implement
    raise NotImplementedError
