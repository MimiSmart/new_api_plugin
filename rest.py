# app.py
import json
from typing import List, Annotated

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body

import ws
from api_models import *
from logic import Logic

home_path = '/home/sh2/exe/new_api_plugin/'  # RELEASE
# home_path = './'  # DEBUG

logic: Logic = None
app = FastAPI(title="MimiSmart API")
manager = None


@app.get("/logic/get/xml", tags=['rest api'], summary="Get logic in xml")
def get_logic_xml():
    return logic.get_xml()


@app.get("/logic/get/obj", tags=['rest api'], summary="Get logic in json")
def get_logic_obj():
    return logic.get_dict()


@app.get("/item/get_attributes/{addr}", tags=['rest api'], response_model=dict,
         response_description='Return dictionary of item attributes',
         summary="Get item if json format")
def get_item(addr: str):
    print(item)
    return logic.get_item(addr)


@app.post("/item/set_attributes", tags=['rest api'], summary="Write/append/remove item")
def set_item(item: Annotated[SetItem, Body(
    examples={
        "write": {"value": {"type": "write", "tag": "item", "area": "System",
                            "data": {"addr": "999:99", "type": "lamp", "name": "Example lamp"}, }},
        "remove": {"value": {"type": "remove", "tag": "item", "area": "System", "data": {"addr": "999:99"}}}
    }, ),], ):
    print(item)
    return logic.set_item(item.type, item.tag, item.area, item.data)


@app.delete("/item/delete", tags=['rest api'], summary="Delete item")
def del_item(item: Annotated[DelItem, Body(example={"addr": "999:99"}, ),], ):
    return logic.del_item(item.addr)


@app.post("/item/get_state/{addr}", tags=['rest api'], response_description='Return string of bytes state',
          summary="Get current state of item")
def get_state(addr: str):
    return logic.get_state(addr)


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
    global manager
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                data = json.loads(data)
                # check if exists command
                if data['command'] in ws.commands:
                    cmd = data['command']
                    data.pop('command')
                    reply = ws.commands[cmd](logic, data)
                else:
                    reply = {'type': 'error', 'message': 'Command not found!'}
            except:
                reply = {'type': 'error', 'message': 'Invalid json!'}
            reply = json.dumps(reply, ensure_ascii=False)
            await websocket.send_text(reply)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def run(host, port, _logic: Logic):
    global app, logic, manager
    logic = _logic
    manager = ConnectionManager()

    # load ws schemas for openapi docs
    with open(home_path + 'websocket_schema.json') as f:
        openapi = app.openapi()
        tmp = json.load(f)
        for key, value in tmp['paths'].items():
            openapi['paths'][key] = value
        for key, value in tmp['schemas'].items():
            openapi['components']['schemas'][key] = value

    uvicorn.run(app, host=host, port=port)
