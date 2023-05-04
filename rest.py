# app.py
from typing import Annotated

from fastapi import FastAPI, Body

from api_models import *
from logic import Logic

home_path = '/home/sh2/exe/new_api_plugin/'  # RELEASE
# home_path = './'  # DEBUG

logic: Logic = None
app = FastAPI(title="MimiSmart API")


def init_logic(_logic: Logic):
    global logic
    logic = _logic


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
