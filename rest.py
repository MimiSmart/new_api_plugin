# app.py
import json
from typing import List

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

import ws
from logic import Logic

logic: Logic = None
app = FastAPI()
manager = None


class Item(BaseModel):
    addr: str


@app.get("/logic/xml")
def get_logic_xml():
    return logic.get_xml()


@app.post("/item/get")
def get_item(item: Item):
    print(item)
    return logic.get_item(item.addr)


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                data = json.loads(data)
                # check if exists command
                if data['command'] in ws.commands:
                    reply = ws.commands[data['command']]()
                else:
                    reply = {'type': 'error', 'message': 'Command not found!'}
            except:
                reply = {'type': 'error', 'message': 'Invalid json!'}
            reply = json.dumps(reply, ensure_ascii=False)
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def run(host, port, _logic: Logic):
    global app, logic
    logic = _logic
    manager = ConnectionManager()

    print('Server run')
    uvicorn.run(app, host=host, port=port)
