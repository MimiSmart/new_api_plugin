import asyncio
import json
import time
import traceback

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

import tools
from auth import Auth
from items import heating
from logic import Logic

subscribes = list()
logic: Logic = None

auth = Auth()
config = tools.read_config()


def init_logic(_logic: Logic):
    global logic
    logic = _logic


def get_items(args):
    return {
        'type': 'response',
        'data': logic.get_dict()
    }


def get_item(args):
    return logic.get_item(*args.values())


def set_item(args):
    return logic.set_item(*args.values())


def del_item(args):
    return logic.del_item(*args.values())


def get_state(args):
    args = args['addr']
    if isinstance(args, str):
        args = [args]

    response = dict()
    for addr in args:
        response[addr] = logic.items[addr].get_state()
    return {'type': 'response', 'data': response}


def get_all_states(args):
    return logic.get_all_states()


def set_state(args):
    global config
    try:

        if 'state' not in args:
            return {"type": "error", "message": "'state' is a required field"}
        if 'addr' not in args:
            return {"type": "error", "message": "'addr' is a required field"}
        if args['addr'] not in logic.items:
            return {"type": "error", "message": f"{args['addr']} not found in logic"}

        # обработка строк, для set_state
        try:
            tmp = [int(args['state'][i:i + 2], 16) for i in
                   range(0, len(args['state']), 2)]  # разбиваем по байтам (2 символа)
        except:
            args['state'] = args['state'].encode('utf-8').hex()
            tmp = [int(args['state'][i:i + 2], 16) for i in
                   range(0, len(args['state']), 2)]  # разбиваем по байтам (2 символа)
        if int(args['addr'].split(':')[0]) < 1000:
            if logic.items[args['addr']].type == 'valve-heating':
                # manual mode
                if tmp[0] in [0, 1]:
                    # set manual mode for heating
                    logic.set_queue.append(('1000:102', [ord(item) for item in f'{args["addr"]}\0as:-4']))

                    # условие поставлено для фикса бага на прошивке RHX
                    if 'fix_manual_heating' in config and config['fix_manual_heating']:
                        state = heating.fix_manual_heating(self=logic.items[args['addr']])
                        return {"type": "response", "data": {args['addr']: list(state)}}
                    else:
                        time.sleep(1.5)

                        # set state for heating
                        logic.set_queue.append((args['addr'], [tmp[0]]))
                # always off
                elif tmp[0] == 2:
                    # set always-off mode for heating
                    logic.set_queue.append(('1000:102', [ord(item) for item in f'{args["addr"]}\0as:-1']))
                # auto
                elif tmp[0] == 3:
                    # write Auto mode to logic.xml, if not exist
                    if logic.write_automation(args["addr"]):
                        # set state with wait upd logic on server 2.0
                        logic.set_queue.append(('1000:102', [ord(item) for item in f'{args["addr"]}\0Auto'], True))
                    else:
                        logic.set_queue.append(('1000:102', [ord(item) for item in f'{args["addr"]}\0Auto']))
                    # set temperature for heating. if 0xFF, then save old temperature
                    if len(tmp) > 1 and tmp[1] != 0xFF:
                        logic.set_queue.append(('1000:102', [ord(item) for item in f'{args["addr"]}\0ts:{tmp[1]}']))
                # others automations (server2.0)
                else:
                    logic.set_queue.append(('1000:102', [ord(item) for item in f'{args["addr"]}\0as:{tmp[0] - 3}']))
                    # set temperature for heating. if 0xFF, then save old temperature
                    if len(tmp) > 1 and tmp[1] != 0xFF:
                        logic.set_queue.append(('1000:102', [ord(item) for item in f'{args["addr"]}\0ts:{tmp[1]}']))
            else:
                logic.set_queue.append((args['addr'], tmp))

            logic.items[args['addr']].set_state(bytes(tmp))
            state = logic.items[args['addr']].get_state()
            # на шторы не возвращаем статус
            if logic.items[args['addr']].type not in ['blinds', 'jalousie', 'gate']:
                return {"type": "response", "data": {args['addr']: state}}
        else:
            logic.set_queue.append((args['addr'], tmp))
    except Exception as ex:
        print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
        return {"type": "error", "message": "Invalid data"}

def get_history(args):
    # если история есть в .hst2 то берем оттуда
    if args['addr'] not in logic.items:
        return {"type": "error", "message": "Item not found"}
    # check correct time
    try:
        # ms
        if args['range_time'][0] > 1000000000000:
            args['range_time'][0] = args['range_time'][0] / 1000
        if args['range_time'][1] > 1000000000000:
            args['range_time'][1] = args['range_time'][1] / 1000
        # float
        args['range_time'][0] = int(args['range_time'][0])
        args['range_time'][1] = int(args['range_time'][1])

    except:
        return {"type": "error", "message": "Invalid data"}

    if not logic.items[args['addr']].hst_supported:
        return {"type": "error", "message": "History is not supported for this item"}

    hst = logic.items[args['addr']].get_history(*args['range_time'], args['scale'])
    if hst:
        return {"type": "response", "addr": args['addr'], "history": hst}
    else:
        # иначе формируем запрос к серверу, ответ будет отправлен клиенту из потока обработчика подписок
        logic.history_requests[args['addr']] = {
            'client': args['client'],
            'requested': False,
            'range_time': args['range_time'],
            'scale': args['scale']
        }


def send_message(args):
    try:
        id, subid = args['addr'].split(':')
        logic.push_requests.append(
            {'id': int(id), 'subid': int(subid), 'message_type': args['message_type'], 'message': args['message']})
        return {"type": "response", "message": 'Push-message send successfully'}
    except:
        return {"type": "error", "message": "Invalid data"}


class SubscribeWebsocket:
    websocket: WebSocket
    event_logic: dict
    event_items: list
    event_statistics: list
    event_msg: list

    # при подписке на элементы сразу отправляются их текущие статусы
    sent_init_status: bool

    authorized: bool = False

    def __init__(self, websocket: WebSocket,
                 event_logic: dict = None,
                 event_items: list = None,
                 event_statistics: list = None,
                 event_msg: list = None):
        self.websocket = websocket
        if event_logic is None:
            self.event_logic = {'logic': False, 'response_type': [], 'items': []}
        else:
            self.event_logic = event_logic
        if event_items is None:
            self.event_items = list()
        else:
            self.event_items = event_items
        if event_statistics is None:
            self.event_statistics = list()
        else:
            self.event_statistics = event_statistics
        if event_msg is None:
            self.event_msg = list()
        else:
            self.event_msg = event_msg
        self.sent_init_status = False


def subscriber(index, args):
    global subscribes, logic
    msg = {'type': 'response'}

    if 'event_logic' in args:
        msg['event_logic'] = {'message': ''}
        # if event_logic is 'all', then make dict with subscribe all
        if isinstance(args['event_logic'], str):
            args['event_logic'] = {'logic': True, 'response_type': ['json', 'xml'], 'items': 'all'}
        if isinstance(args['event_logic'], dict):
            if 'logic' in args['event_logic'] and args['event_logic']['logic']:
                if args['command'] == 'subscribe':
                    subscribes[index].event_logic['logic'] = True
                    # отправляю логику в xml сразу при подписке
                    msg['event_logic']['xml'] = logic.get_xml().decode('utf-8')
                    msg['event_logic']['message'] += "Subscribe logic success\n"
                # unsubscribe
                else:
                    subscribes[index].event_logic['logic'] = False
                    msg['event_logic']['message'] += "Unsubscribe logic success\n"
            if 'response_type' in args['event_logic']:
                if isinstance(args['event_logic']['response_type'], str):
                    args['event_logic']['response_type'] = [args['event_logic']['response_type']]
                if args['command'] == 'subscribe':
                    for response_type in args['event_logic']['response_type']:
                        if response_type not in subscribes[index].event_logic['response_type']:
                            subscribes[index].event_logic['response_type'].append(response_type)
                    # отправляю логику в json сразу при подписке
                    if 'json' in subscribes[index].event_logic['response_type']:
                        msg['event_logic']['json'] = logic.get_dict()
                # unsubscribe
                else:
                    for response_type in args['event_logic']['response_type']:
                        if response_type in subscribes[index].event_logic['response_type']:
                            subscribes[index].event_logic['response_type'].remove(response_type)
                    if not len(subscribes[index].event_logic['response_type']):
                        subscribes[index].event_logic['response_type'].append('json')

            # by default logic response type is json
            elif args['command'] == 'subscribe' and 'json' not in subscribes[index].event_logic['response_type']:
                subscribes[index].event_logic['response_type'].append('json')
            if 'items' in args['event_logic']:
                if isinstance(args['event_logic']['items'], str):
                    # if 'items' is 'all'
                    if args['event_logic']['items'] == 'all':
                        if args['command'] == 'subscribe':
                            # append all existed items to subscribe
                            for item in logic.items.values():
                                subscribes[index].event_logic['items'].append(item.addr)
                            # remove duplicates
                            subscribes[index].event_logic['items'] = \
                                list(set(subscribes[index].event_logic['items']))
                            # msg['event_logic'] += "Subscribe all items success\n"
                        # unsubscribe
                        else:
                            for x in range(len(subscribes[index].event_logic['items'])):
                                subscribes[index].event_logic['items'].pop()
                            msg['event_logic']['message'] += "Unsubscribe all items success\n"
                    # if 'items' is string addr item, then make list with this one item
                    else:
                        args['event_logic']['items'] = [args['event_logic']['items']]
                # list of items
                if isinstance(args['event_logic']['items'], list):
                    if args['command'] == 'subscribe':
                        items = [item.addr for item in logic.items.values()]
                        flag = False
                        # search for subscribed items in existed items
                        for item in args['event_logic']['items']:
                            if item in items:
                                subscribes[index].event_logic['items'].append(item)
                            else:
                                flag = True
                                msg['event_logic']['message'] += "Item %s not found in logic\n" % (str(item))
                        if not flag:
                            msg['event_logic']['message'] += "Subscribe items success\n"
                    # unsubscribe
                    else:
                        not_found_items = []
                        for item in args['event_logic']['items']:
                            # 'try' block need if item not in list
                            try:
                                subscribes[index].event_logic['items'].remove(item)
                            except:
                                not_found_items.append(item)
                        if len(not_found_items):
                            msg['event_logic']['message'] += "Subscription items %s not found!\n" % (
                                str(not_found_items))
                        else:
                            msg['event_logic']['message'] += "Unsubscribe success\n"
        # remove last \n
        if len(msg['event_logic']):
            msg['event_logic']['message'] = msg['event_logic']['message'][:-1]
    if 'event_msg' in args:
        if args['command'] == 'subscribe':
            if args['event_msg'] == 'all':
                for i in range(0x90):
                    subscribes[index].event_msg.append(i)
            else:
                if not isinstance(args['event_msg'], list):
                    args['event_msg'] = [args['event_msg']]
                for msg in args['event_msg']:
                    subscribes[index].event_msg.append(msg)
            # remove duplicates
            subscribes[index].event_msg = list(set(subscribes[index].event_msg))
            msg['event_msg'] = 'Subscribe success'
        # unsubscribe
        else:
            if args['event_msg'] == 'all':
                subscribes[index].event_msg = list()
            else:
                if not isinstance(args['event_msg'], list):
                    args['event_msg'] = [args['event_msg']]
                for msg in args['event_msg']:
                    index = subscribes[index].event_msg.index(msg)
                    subscribes[index].event_msg.pop(index)
            msg['event_msg'] = 'Unsubscribe success'
    if 'event_items' in args:
        msg['event_items'] = ''
        # if event_items is string addr of item, then make list with this one addr
        if isinstance(args['event_items'], str) and args['event_items'] != 'all':
            args['event_items'] = [args['event_items']]
        # if event_items is list of addr items
        if isinstance(args['event_items'], list):
            if args['command'] == 'subscribe':
                # search all existed items in logic
                items = [item.addr for item in logic.items.values()]
                # search for subscribed items in existed items
                for item in args['event_items']:
                    if item in items:
                        subscribes[index].event_items.append(item)
                    else:
                        msg['event_items'] += "Item %s not found in logic\n" % (str(item))
                # remove duplicates
                subscribes[index].event_items = \
                    list(set(subscribes[index].event_items))
                subscribes[index].sent_init_status = False
                if not msg['event_items']:
                    msg['event_items'] += "Subscribe success\n"
            # unsubscribe
            else:
                not_found_items = []
                for item in args['event_items']:
                    # 'try' block need if item not in list
                    try:
                        subscribes[index].event_items.remove(item)
                    except:
                        not_found_items.append(item)
                if len(not_found_items):
                    msg['event_items'] += "Subscription items %s not found!\n" % (str(not_found_items))
                else:
                    msg['event_items'] += "Unsubscribe success\n"
        # if event_items is 'all'
        elif isinstance(args['event_items'], str):
            if args['event_items'] == 'all':
                if args['command'] == 'subscribe':
                    # append all existed items to subscribe
                    for item in logic.items.values():
                        subscribes[index].event_items.append(item.addr)
                    # remove duplicates
                    subscribes[index].event_items = \
                        list(set(subscribes[index].event_items))
                    subscribes[index].sent_init_status = False
                    msg['event_items'] += "Subscribe all success\n"
                # unsubscribe
                else:
                    for x in range(len(subscribes[index].event_items)):
                        subscribes[index].event_items.pop()
                    msg['event_items'] += "Unsubscribe all success\n"
            else:
                msg['event_items'] += "'event_items' supported only 'all', str addr or list of items\n"

        # remove last \n
        if len(msg['event_items']):
            msg['event_items'] = msg['event_items'][:-1]
    if 'event_statistics' in args:
        msg['event_statistics'] = ''
        if isinstance(args['event_statistics'], str):
            if ':' in args['event_statistics']:
                args['event_statistics'] = [args['event_statistics']]
            elif args['event_statistics'] == 'all':
                if args['command'] == 'subscribe':
                    # append all existed items to subscribe
                    for item in logic.items.values():
                        subscribes[index].event_statistics.append(item.addr)
                    # remove duplicates
                    subscribes[index].event_statistics = \
                        list(set(subscribes[index].event_statistics))
                    msg['event_statistics'] += "Subscribe all success\n"
                # unsubscribe
                else:
                    for x in range(len(subscribes[index].event_statistics)):
                        subscribes[index].event_statistics.pop()
                    msg['event_statistics'] += "Unsubscribe all success\n"
            else:
                msg['event_statistics'] += "'event_statistics' supported only 'all', str addr or list of items\n"
        if isinstance(args['event_statistics'], list):
            if args['command'] == 'subscribe':
                # search all existed items in logic
                items = [item.addr for item in logic.items.values()]
                # search for subscribed items in existed items
                for item in args['event_statistics']:
                    if item in items:
                        subscribes[index].event_statistics.append(item)
                    else:
                        msg['event_statistics'] += "Item %s not found in logic\n" % (str(item))
                # remove duplicates
                subscribes[index].event_statistics = \
                    list(set(subscribes[index].event_statistics))
                if not msg['event_statistics']:
                    msg['event_statistics'] += "Subscribe success\n"
            # unsubscribe
            else:
                not_found_items = []
                for item in args['event_statistics']:
                    # 'try' block need if item not in list
                    try:
                        subscribes[index].event_statistics.remove(item)
                    except:
                        not_found_items.append(item)
                if len(not_found_items):
                    msg['event_statistics'] += "Subscription items %s not found!\n" % (str(not_found_items))
                else:
                    msg['event_statistics'] += "Unsubscribe success\n"
        # subscribes[index].event_statistics = args['event_statistics']

        # remove last \n
        if len(msg['event_statistics']):
            msg['event_statistics'] = msg['event_statistics'][:-1]

    return msg


async def ws_send_message(websocket: WebSocket, message):
    message = json.dumps(message, ensure_ascii=False)

    try:
        await websocket.send_text(message)
        print(f"Websocket send data: {message} length:{len(message)}")
    except:
        pass


def find_index(websocket):
    global subscribes
    for cntr in range(len(subscribes)):
        if subscribes[cntr].websocket == websocket:
            return cntr
    return None


async def authorize(args):
    global subscribes
    result = await auth.get_current_user(args['access_token'])
    if result:
        subscribes[args['index']].authorized = True
        return {'type': 'response', 'message': 'Authorize success!'}
    else:
        return {'type': 'error', 'message': 'Invalid token'}


def get_token(args):
    result = auth.authenticate_user(args['password'])
    if result:
        return result
    else:
        return {'type': 'error', 'message': 'Username or password is incorrect'}


async def endpoint(websocket: WebSocket):
    global subscribes, commands, config

    # добавление нового коннекшна
    subscribes.append(SubscribeWebsocket(websocket))
    await websocket.accept()

    # --------------------------------
    try:
        # обработка сообщений от клиента
        while True:
            reply = None
            data = await websocket.receive_text()
            try:
                data = json.loads(data)
                print(f"Websocket received: {data}")

                # check if exists command
                if data['command'] in commands:
                    # авторизация по вебсокету
                    if data['command'] == 'auth' and config['auth']:
                        data['index'] = find_index(websocket)
                        cmd = data['command']
                        data.pop('command')
                        reply = await authorize(data)
                    elif data['command'] == 'get_token' and config['auth']:
                        cmd = data['command']
                        data.pop('command')
                        reply = commands[cmd](data)
                    elif subscribes[find_index(websocket)].authorized or not config['auth']:  # debug config auth
                        if data['command'] == 'subscribe' or data['command'] == 'unsubscribe':
                            reply = subscriber(find_index(websocket), data)
                        else:
                            if data['command'] == 'get_history':
                                data['client'] = websocket
                            cmd = data['command']
                            data.pop('command')
                            reply = commands[cmd](data)
                    else:
                        reply = {'type': 'error', 'message': 'Not authorized!'}
                else:
                    reply = {'type': 'error', 'message': 'Command not found!'}
            except:
                reply = {'type': 'error', 'message': 'Invalid json!'}

            try:
                if reply:
                    await ws_send_message(websocket, reply)
            except Exception as err:
                await websocket.close()
                subscribes.pop(find_index(websocket))

                print(f"Error send data to websocket. Data: {json.dumps(reply)}")
                print(f"Unexpected {err=}, {type(err)=}")
    # disconnect client
    except WebSocketDisconnect:
        subscribes.pop(find_index(websocket))


def listener():
    def ws_not_connected(index):
        addr = ':'.join(str(x) for x in [*subscribes[index].websocket.client])
        print(f"Websocket {addr} state is not connected. Close connection")
        asyncio.run(subscribes[index].websocket.close())
        subscribes.pop(index)

    print('Websocket event listener for subscribers started')
    global subscribes, logic
    old_states = dict()
    while True:
        length = len(subscribes)
        for index in range(length):
            if index >= length:
                break
            # handle response for get_history requests (partial, only if history from server 2.0)
            if logic.history_requests:
                copy = logic.history_requests.copy()
                for key, item in copy.items():
                    if 'responsed' in item and logic.items[key].history:
                        hst = logic.items[key].get_history(*item['range_time'], item['scale'], wait=True)
                        response = {'type': 'response', 'history': hst, 'addr': key}
                        logic.history_requests.pop(key)
                        if item['client'].client_state is WebSocketState.CONNECTED:
                            asyncio.run(ws_send_message(item['client'], response))  # if client connected
                        else:
                            ws_not_connected(index)
                            break

            if subscribes[index].event_msg:
                pushes = list()
                for push in logic.push_events:
                    if push['type'] in subscribes[index].event_msg:
                        pushes.append(push)
                # упаковываем все однотипные ивенты в 1 пакет
                if pushes:
                    response = {'type': 'subscribe-event', 'event_type': "push_message",
                                'data': pushes}
                    if subscribes[index].websocket.client_state is WebSocketState.CONNECTED:
                        asyncio.run(ws_send_message(subscribes[index].websocket, response))
                    else:
                        ws_not_connected(index)
                        break
            if subscribes[index].event_logic['logic'] and logic.update_flag:
                if logic.logic_update:
                    if 'json' in subscribes[index].event_logic['response_type']:
                        msg = logic.get_dict()
                        response = {'type': 'subscribe-event', 'event_type': "logic_json_update", 'data': msg}
                        if subscribes[index].websocket.client_state is WebSocketState.CONNECTED:
                            asyncio.run(ws_send_message(subscribes[index].websocket, response))
                        else:
                            ws_not_connected(index)
                            break
                    if 'xml' in subscribes[index].event_logic['response_type']:
                        msg = logic.get_xml().decode('utf-8')
                        response = {'type': 'subscribe-event', 'event_type': "logic_xml_update", 'data': msg}
                        if subscribes[index].websocket.client_state is WebSocketState.CONNECTED:
                            asyncio.run(ws_send_message(subscribes[index].websocket, response))
                        else:
                            ws_not_connected(index)
                            break
            if subscribes[index].event_logic['items'] and logic.update_flag:
                msg = dict()
                for addr in subscribes[index].event_logic['items']:
                    if addr in logic.items.keys() and logic.items[addr].update:
                        msg[addr] = logic.items[addr].json_obj
                # упаковываем все однотипные ивенты в 1 пакет
                if msg:
                    response = {'type': 'subscribe-event', 'event_type': "logic_item_update",
                                'data': msg}
                    if subscribes[index].websocket.client_state is WebSocketState.CONNECTED:
                        asyncio.run(ws_send_message(subscribes[index].websocket, response))
                    else:
                        ws_not_connected(index)
                        break
            if subscribes[index].event_items:
                msg = list()
                for addr in subscribes[index].event_items:
                    if addr in logic.items.keys() and logic.items[addr].state is not None:
                        new_state = logic.items[addr].state
                        # if new state not equal old state, then send event
                        if not subscribes[index].sent_init_status or addr not in old_states \
                                or old_states[addr] != new_state:
                            msg.append({addr: new_state.hex(' ')})
                            # msg[addr] = new_state.hex(' ')
                if not subscribes[index].sent_init_status:
                    subscribes[index].sent_init_status = True
                # упаковываем все однотипные ивенты в 1 пакет
                if msg:
                    response = {'type': 'subscribe-event', 'event_type': "state_item",
                                'data': msg}
                    if subscribes[index].websocket.client_state is WebSocketState.CONNECTED:
                        asyncio.run(ws_send_message(subscribes[index].websocket, response))
                    else:
                        ws_not_connected(index)
                        break
            if subscribes[index].event_statistics:
                if logic.history_events:
                    msg = dict()
                    for addr, state in logic.history_events.items():
                        if addr in subscribes[index].event_statistics:
                            msg[addr] = state.hex(' ')  # debug
                    # упаковываем все однотипные ивенты в 1 пакет
                    if msg:
                        response = {'type': 'subscribe-event', 'event_type': "statistics", 'data': msg}
                        if subscribes[index].websocket.client_state is WebSocketState.CONNECTED:
                            asyncio.run(ws_send_message(subscribes[index].websocket, response))
                        else:
                            ws_not_connected(index)
                            break
            length = len(subscribes)

        # avoid exception: 'dictionary changed size during iteration'
        tmp_items = logic.items.copy()
        # запоминаем все текущие стейты
        for addr, item in tmp_items.items():
            old_states[addr] = item.state

        if logic.update_flag:
            # обнуляем флаги обновления логики
            if logic.logic_update:
                logic.logic_update = False
            for addr, item in logic.items.items():
                item.update = False
            logic.update_flag = False

        if logic.history_events:
            logic.history_events = dict()

        if logic.push_events:
            logic.push_events = list()

        time.sleep(0.3)


commands = {
    "get_items": get_items,
    "get_item": get_item,
    "set_item": set_item,
    "del_item": del_item,
    "get_state": get_state,
    "get_all_states": get_all_states,
    "set_state": set_state,
    "get_history": get_history,
    "send_message": send_message,
    "subscribe": subscriber,
    "unsubscribe": subscriber,
    "auth": authorize,
    "get_token": get_token

}
