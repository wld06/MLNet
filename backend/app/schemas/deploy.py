from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeploymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    name: str
    endpoint_url: str | None
    status: str
    created_at: datetime
    request_count: int
    last_called_at: datetime | None


class PredictRequest(BaseModel):
    features: dict


class PredictResponse(BaseModel):
    prediction: float | int | str | list
    probabilities: dict | None = None
