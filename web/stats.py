# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import List
from sqlalchemy import select, and_
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from core.ops.operator import async_ops
from core.ops.schema import Account
from core.event import MetricEvent
from .login import get_current_user

router = APIRouter()


@router.get("/on_stats")
async def on_query_account(event: MetricEvent):
    user = await get_current_user(event.token)
    req = select(Account).where(and_(Account.user == user.id, 
                                     Account.experiments.c.experiment_id == event.experiment_id,
                                     Account.date <= event.end_dt,
                                     Account.date >= event.start_dt))
    obj = await async_ops.on_query_obj(req)
    return obj


# broadcast
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()


@router.websocket("/ws/broadcast")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Broadcast: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, token: str):
    if token != "secure_token":  # Example token validation
        await websocket.close(code=1008)  # Policy violation
        raise HTTPException(status_code=403, detail="Unauthorized")

    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Client {client_id} says: {data}")
    except WebSocketDisconnect:
        print(f"Client {client_id} disconnected")

# Connect to ws://127.0.0.1:8000/ws/1234?token=secure_token.
 


@router.get("/api")
def api():
    return {"metrics": "metrics"}
