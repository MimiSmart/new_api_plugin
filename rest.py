# app.py
import json
from typing import List

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

import ws
from logic import Logic

logic: Logic = None
app = FastAPI(title="MimiSmart API")
manager = None


class GetItem(BaseModel):
    addr: str


class SetItem(BaseModel):
    type: str = Field(title="Operation type (write, append, remove)")
    tag: str = Field(title="Tag of item ('item', 'area', etc.)")
    area: str = Field(title="Name of area. if set item in root - set 'smart-house'")
    data: dict = Field(title="Attributes and childs of added item in format key:value")


@app.get("/logic/get/xml", tags=['rest api'])
def get_logic_xml():
    return logic.get_xml()


@app.get("/logic/get/obj", tags=['rest api'])
def get_logic_obj():
    return logic.get_dict()


@app.post("/item/get_attributes", tags=['rest api'], response_model=dict,
          response_description='Return dictionary of item attributes')
def get_item(item: GetItem):
    print(item)
    return logic.get_item(item.addr)


@app.post("/item/set_attributes", tags=['rest api'])
def set_item(item: SetItem):
    print(item)
    return logic.set_item(item.type, item.tag, item.area, item.data)


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

    # load ws schemas for openapi docs
    with open('websocket_schema.json') as f:
        openapi = app.openapi()
        tmp = json.load(f)
        for key, value in tmp['paths'].items():
            openapi['paths'][key] = value
        for key, value in tmp['schemas'].items():
            openapi['components']['schemas'][key] = value

    uvicorn.run(app, host=host, port=port)
