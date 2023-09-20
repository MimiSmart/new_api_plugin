import json
from typing import Annotated

from fastapi import FastAPI, Body, Response, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from api_models import SetState, SetLogic, GetState, SetItem, GetHistory, SendMessage
from auth import Auth
from logic import Logic

logic: Logic = None
app = FastAPI(title="MimiSmart API")

auth = Auth()


def __init__(_logic: Logic):
    global logic
    logic = _logic


def convert2response(msg):
    if type(msg) is dict:
        return Response(content=json.dumps(msg, ensure_ascii=False),
                        headers={'Access-Control-Allow-Origin': '*'})
    else:
        return Response(content=msg,
                        headers={'Access-Control-Allow-Origin': '*'})


@app.post("/logic/get/xml", tags=['rest api'], summary="Get logic in xml")
def get_logic_xml(current_user: Annotated[auth.User, Depends(auth.get_current_user)]):
    return convert2response(logic.get_xml())


@app.post("/logic/get/obj", tags=['rest api'], summary="Get logic in json")
def get_logic_obj(current_user: Annotated[auth.User, Depends(auth.get_current_user)]):
    return convert2response(logic.get_dict())


@app.post("/logic/set/xml", tags=['rest api'], summary="Write logic.xml")
def set_logic_xml(current_user: Annotated[auth.User, Depends(auth.get_current_user)], item: SetLogic):
    return convert2response(
        {'type': 'response', 'message': 'Write successfully'}
        if logic.set_xml(item.xml) else
        {'type': 'error', 'message': 'Error write'}
    )


@app.post("/item/get_attributes/{addr}", tags=['rest api'], response_model=dict,
         response_description='Return dictionary of item attributes',
         summary="Get item if json format")
def get_item(current_user: Annotated[auth.User, Depends(auth.get_current_user)], addr: str):
    return convert2response(logic.get_item(addr))


@app.post("/item/set_attributes", tags=['rest api'], summary="Write/append/remove item")
def set_item(current_user: Annotated[auth.User, Depends(auth.get_current_user)], item: Annotated[SetItem, Body(
    examples={
        "write": {"value": {"type": "write", "tag": "item", "area": "System",
                            "data": {"addr": "999:99", "type": "lamp", "name": "Example lamp"}, }},
        "remove": {"value": {"type": "remove", "tag": "item", "area": "System", "data": {"addr": "999:99"}}}
    }, ),], ):
    return convert2response(logic.set_item(item.type, item.tag, item.area, item.data))


@app.post("/item/delete/{addr}", tags=['rest api'], summary="Delete item")
# def del_item(item: Annotated[DelItem, Body(example={"addr": "999:99"}, ),], ):
def del_item(current_user: Annotated[auth.User, Depends(auth.get_current_user)], addr: str):
    return convert2response(logic.del_item(addr))


@app.post("/item/get_state/", tags=['rest api'], response_description='Return string of bytes state',
          summary="Get current state of item")
def get_state(current_user: Annotated[auth.User, Depends(auth.get_current_user)], item: GetState):
    args = item.addr
    if isinstance(args, str):
        args = [args]

    response = dict()
    for addr in args:
        response[addr] = logic.items[addr].get_state()
    return convert2response({'type': 'response', 'data': response})


@app.post("/item/get_all_states/", tags=['rest api'], response_description='Return string of bytes state',
         summary="Get all current states of item")
def get_all_states(current_user: Annotated[auth.User, Depends(auth.get_current_user)]):
    return convert2response(logic.get_all_states())


@app.post("/item/set_state/", tags=['rest api'], summary="Set state on item")
def set_state(current_user: Annotated[auth.User, Depends(auth.get_current_user)], item: SetState):
    try:

        if item.addr not in logic.items:
            return convert2response({"type": "error", "message": f"{item.addr} not found in logic"})

        # обработка строк, для set_state
        try:
            tmp = [int(item.state[i:i + 2], 16) for i in
                   range(0, len(item.state), 2)]  # разбиваем по байтам (2 символа)
        except:
            item.state = item.state.encode('utf-8').hex()
            tmp = [int(item.state[i:i + 2], 16) for i in
                   range(0, len(item.state), 2)]  # разбиваем по байтам (2 символа)

        if logic.items[item.addr].type == 'valve-heating':
            # set temperature for heating
            logic.set_queue.append(('1000:102', [ord(x) for x in f'{item.addr}\0ts:{tmp[1]}']))
            # manual off
            if tmp[0] == 0:
                # set manual mode for heating
                logic.set_queue.append(('1000:102', [ord(x) for x in f'{item.addr}\0as:-4']))
                # set 0 for heating
                logic.set_queue.append((item.addr, [0]))
            # manual on
            elif tmp[0] == 1:
                # set manual mode for heating
                logic.set_queue.append(('1000:102', [ord(x) for x in f'{item.addr}\0as:-4']))
                # set 0 for heating
                logic.set_queue.append((item.addr, [1]))
            # always off
            elif tmp[0] == 2:
                # set always-off mode for heating
                logic.set_queue.append(('1000:102', [ord(x) for x in f'{item.addr}\0as:1']))
            # auto and others automations (server2.0)
            else:
                logic.set_queue.append(('1000:102', [ord(x) for x in f'{item.addr}\0as:{tmp[0] - 3}']))
                # set temperature for heating. if 0xFF, then save old temperature
                if tmp[1] != 0xFF:
                    logic.set_queue.append(('1000:102', [ord(x) for x in f'{item.addr}\0ts:{tmp[1]}']))
        else:
            logic.set_queue.append((item.addr, tmp))

        logic.items[item.addr].set_state(bytes(tmp))
        state = logic.items[item.addr].get_state()

        return convert2response({"type": "response", "data": {item.addr: state}})
    except:
        return convert2response({"type": "error", "message": "Invalid data"})


@app.post("/item/get_history/", tags=['rest api'], summary="Set state on item")
def get_history(current_user: Annotated[auth.User, Depends(auth.get_current_user)], args: GetHistory):
    # если история есть в .hst2 то берем оттуда
    if args.addr not in logic.items:
        return convert2response({"type": "error", "message": "Item not found"})
    # check correct time
    try:
        # ms
        if args.range_time[0] > 1000000000000:
            args.range_time[0] = int(args.range_time[0] / 1000)
        if args.range_time[1] > 1000000000000:
            args.range_time[1] = int(args.range_time[1] / 1000)
        # float
        args.range_time[0] = int(args.range_time[0])
        args.range_time[1] = int(args.range_time[1])
    except:
        return {"type": "error", "message": "Invalid data"}

    # обработка запроса для итемов, которые не поддерживают историю
    if not logic.items[args.addr].hst_supported:
        return convert2response({"type": "error", "message": "History is not supported for this item"})
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
def send_message(current_user: Annotated[auth.User, Depends(auth.get_current_user)], args: SendMessage):
    try:
        id, subid = args.addr.split(':')
        logic.push_requests.append(
            {'id': int(id), 'subid': int(subid), 'message_type': args.message_type, 'message': args.message})
        return convert2response({"type": "response", "message": 'Push-message send successfully'})
    except:
        return convert2response({"type": "error", "message": "Invalid data"})


@app.post("/token", response_model=auth.Token, tags=['rest api'], summary="Get access token", )
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    result = auth.authenticate_user(form_data.password)
    if not result or form_data.username != 'mimismart':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result
