from app.db.session import SessionLocal
from app.services.training_service import train_run
from app.workers.celery_app import celery_app


@celery_app.task(bind=True, name="training.run_experiment")
def run_experiment_task(self, experiment_id: int, run_id: int) -> dict:
    db = SessionLocal()
    try:
        return train_run(db, experiment_id, run_id)
    finally:
        db.close()
