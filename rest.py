# app.py
import json
from threading import Thread
from typing import Annotated

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Body

import ws
from api_models import *
from logic import Logic

home_path = '/home/sh2/exe/new_api_plugin/'  # RELEASE
# home_path = './'  # DEBUG

logic: Logic = None
app = FastAPI(title="MimiSmart API")


@app.on_event("startup")
async def startup_event():
    global logic, subscribes
    print('fastapi started')
    ws_event_listener_thread = Thread(target=ws.event_listener,
                                      args=[logic, subscribes],
                                      name='ws subscribe events')
    ws_event_listener_thread.start()
    print('Websocket event listener for subscribers started')


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


@app.get("/item/get_state/{addr}", tags=['rest api'], response_description='Return string of bytes state',
         summary="Get current state of item")
def get_state(addr: str):
    return logic.get_state(addr)


@app.get("/item/get_all_states/", tags=['rest api'], response_description='Return string of bytes state',
         summary="Get all current states of item")
def get_all_states():
    return logic.get_all_states()


subscribes = list()


def find_index(subscribes, websocket):
    for cntr in range(len(subscribes)):
        if subscribes[cntr].websocket == websocket:
            return cntr


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    global subscribes

    subscribes.append(ws.SubscribeWebsocket(websocket))
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            try:
                data = json.loads(data)
                # check if exists command
                if data['command'] in ws.commands:

                    if data['command'] == 'subscribe' or data['command'] == 'unsubscribe':
                        reply = ws.subscriber(logic, subscribes, find_index(subscribes, websocket), data)
                    else:
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
        subscribes.pop(find_index(subscribes, websocket))


def run(host, port, _logic: Logic):
    global app, logic
    logic = _logic

    # load ws schemas for openapi docs
    with open(home_path + 'websocket_schema.json') as f:
        openapi = app.openapi()
        tmp = json.load(f)
        for key, value in tmp['paths'].items():
            openapi['paths'][key] = value
        for key, value in tmp['schemas'].items():
            openapi['components']['schemas'][key] = value

    uvicorn.run(app, host=host, port=port)
