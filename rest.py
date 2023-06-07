# app.py
import json
from typing import Annotated

from fastapi import FastAPI, Body, Response

from api_models import *
from logic import Logic

home_path = '/home/sh2/exe/new_api_plugin/'  # RELEASE
# home_path = './'  # DEBUG

logic: Logic = None
app = FastAPI(title="MimiSmart API")


def init_logic(_logic: Logic):
    global logic
    logic = _logic


def convert2response(msg):
    if type(msg) is dict:
        return Response(content=json.dumps(msg, ensure_ascii=False),
                        headers={'Access-Control-Allow-Origin': '*'})
    else:
        return Response(content=msg,
                        headers={'Access-Control-Allow-Origin': '*'})


@app.get("/logic/get/xml", tags=['rest api'], summary="Get logic in xml")
def get_logic_xml():
    return convert2response(logic.get_xml())


@app.get("/logic/get/obj", tags=['rest api'], summary="Get logic in json")
def get_logic_obj():
    return convert2response(logic.get_dict())


@app.post("/logic/set/xml", tags=['rest api'], summary="Write logic.xml")
def set_logic_xml(item: SetLogic):
    return convert2response(
        {'type': 'response', 'message': 'Write successfully'}
        if logic.set_xml(item.xml) else
        {'type': 'error', 'message': 'Error write'}
    )


@app.get("/item/get_attributes/{addr}", tags=['rest api'], response_model=dict,
         response_description='Return dictionary of item attributes',
         summary="Get item if json format")
def get_item(addr: str):
    return convert2response(logic.get_item(addr))


@app.post("/item/set_attributes", tags=['rest api'], summary="Write/append/remove item")
def set_item(item: Annotated[SetItem, Body(
    examples={
        "write": {"value": {"type": "write", "tag": "item", "area": "System",
                            "data": {"addr": "999:99", "type": "lamp", "name": "Example lamp"}, }},
        "remove": {"value": {"type": "remove", "tag": "item", "area": "System", "data": {"addr": "999:99"}}}
    }, ),], ):
    return convert2response(logic.set_item(item.type, item.tag, item.area, item.data))


@app.delete("/item/delete/{addr}", tags=['rest api'], summary="Delete item")
# def del_item(item: Annotated[DelItem, Body(example={"addr": "999:99"}, ),], ):
def del_item(addr: str):
    return convert2response(logic.del_item(addr))


@app.post("/item/get_state/", tags=['rest api'], response_description='Return string of bytes state',
          summary="Get current state of item")
def get_state(item: GetState):
    return convert2response(logic.get_state(item.addr))


@app.get("/item/get_all_states/", tags=['rest api'], response_description='Return string of bytes state',
         summary="Get all current states of item")
def get_all_states():
    return convert2response(logic.get_all_states())


@app.post("/item/set_state/", tags=['rest api'], summary="Set state on item")
def set_state(item: SetState):
    item.state = [int(item.state[i:i + 2]) for i in range(0, len(item.state), 2)]  # разбиваем по байтам (2 символа)
    logic.set_queue.append((item.addr, item.state))
    # return convert2response()


@app.post("/item/get_history/", tags=['rest api'], summary="Set state on item")
def get_history(args: GetHistory):
    # если история есть в .hst2 то берем оттуда
    if args.addr not in logic.items:
        return convert2response({"type": "error", "message": "Item not found"})
    hst = logic.items[args.addr].get_history(*args.range_time, args.scale)
    if not hst:
        # иначе формируем запрос к серверу и ждем ответа с таймаутом 1 сек
        logic.history_requests[args.addr] = {
            'requested': False,
            'range_time': args.range_time,
            'scale': args.scale
        }
        hst = logic.items[args.addr].get_history(*args.range_time, args.scale, wait=True)
    return convert2response({"type": "response", "addr": args.addr, "history": hst})


@app.post("/item/send_message/", tags=['rest api'], summary="Send push message")
def send_message(args: SendMessage):
    try:
        id, subid = args.addr.split(':')
        logic.push_requests.append(
            {'id': int(id), 'subid': int(subid), 'message_type': args.message_type, 'message': args.message})
        return convert2response({"type": "response", "message": 'Push-message send successfully'})
    except:
        return convert2response({"type": "error", "message": "Invalid data"})
