"""WebSocket endpoints streaming live progress from Redis pub/sub channels."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.events import cleaning_channel, experiment_channel, subscribe

router = APIRouter(tags=["websocket"])


async def _stream(websocket: WebSocket, channel: str) -> None:
    await websocket.accept()
    try:
        async for event in subscribe(channel):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/experiments/{experiment_id}")
async def experiment_progress(websocket: WebSocket, experiment_id: int) -> None:
    await _stream(websocket, experiment_channel(experiment_id))


@router.websocket("/ws/datasets/{dataset_id}/clean")
async def cleaning_progress(websocket: WebSocket, dataset_id: int) -> None:
    await _stream(websocket, cleaning_channel(dataset_id))
