from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="training.run_experiment")
def run_experiment_task(self, experiment_id: int, run_id: int) -> dict:
    # TODO: implement
    raise NotImplementedError
