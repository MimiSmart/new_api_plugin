import asyncio
import json
import time

from fastapi import WebSocket, WebSocketDisconnect

from logic import Logic

subscribes = list()
logic: Logic = None


def init_logic(_logic: Logic):
    global logic
    logic = _logic


def test(logic: Logic, args):
    return {
        'type': 'response',
        'message': "test completed"
    }


def get_items(logic: Logic, args):
    return {
        'type': 'response',
        'data': logic.get_dict()
    }


def get_item(logic: Logic, args):
    return logic.get_item(*args.values())


def set_item(logic: Logic, args):
    return logic.set_item(*args.values())


def del_item(logic: Logic, args):
    return logic.del_item(*args.values())


def get_state(logic: Logic, args):
    return logic.get_state(*args.values())


def get_all_states(logic: Logic, args):
    return logic.get_all_states()


def set_state(logic: Logic, args):
    args['state'] = [int(args['state'][i:i + 2]) for i in range(0, len(args['state']), 2)]  # разбиваем по байтам (2 символа)
    logic.set_queue.append((args['addr'], args['state']))


class SubscribeWebsocket:
    websocket: WebSocket
    event_logic: dict
    event_items: list
    event_statistics: list
    event_msg: bool

    def __init__(self, websocket: WebSocket,
                 event_logic: dict = None,
                 event_items: list = None,
                 event_statistics: list = None,
                 event_msg: bool = False):
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
        self.event_msg = event_msg


def subscriber(index, args):
    global subscribes, logic
    msg = {'type': 'response'}

    if 'event_logic' in args:
        msg['event_logic'] = ''
        # if event_logic is 'all', then make dict with subscribe all
        if isinstance(args['event_logic'], str):
            args['event_logic'] = {'logic': True, 'response_type': ['json', 'xml'], 'items': 'all'}
        if isinstance(args['event_logic'], dict):
            if 'logic' in args['event_logic'] and args['event_logic']['logic']:
                if args['command'] == 'subscribe':
                    subscribes[index].event_logic['logic'] = True
                    msg['event_logic'] += "Subscribe logic success\n"
                # unsubscribe
                else:
                    subscribes[index].event_logic['logic'] = False
                    msg['event_logic'] += "Unsubscribe logic success\n"
            if 'response_type' in args['event_logic']:
                if isinstance(args['event_logic']['response_type'], str):
                    args['event_logic']['response_type'] = [args['event_logic']['response_type']]
                if args['command'] == 'subscribe':
                    for response_type in args['event_logic']['response_type']:
                        if response_type not in subscribes[index].event_logic['response_type']:
                            subscribes[index].event_logic['response_type'].append(response_type)
                # unsubscribe
                else:
                    for response_type in args['event_logic']['response_type']:
                        if response_type not in subscribes[index].event_logic['response_type']:
                            subscribes[index].event_logic['response_type'].remove(response_type)
                    if not len(subscribes[index].event_logic['response_type']):
                        subscribes[index].event_logic['response_type'].append('json')
                        msg['event_logic'] += "Incorrect unsubscribe logic response type. The response \
                            type can`t be empty, json format will be used by default. If you want to \
                            unsubscribe from logic updates - use 'logic:false'\n"

            # by default logic response type is json
            elif args['command'] == 'subscribe' and 'json' not in subscribes[index].event_logic['response_type']:
                subscribes[index].event_logic['response_type'].append('json')
            if 'items' in args['event_logic']:
                if isinstance(args['event_logic']['items'], str):
                    # if 'items' is 'all'
                    if args['event_logic']['items'] == 'all':
                        if args['command'] == 'subscribe':
                            # append all existed items to subscribe
                            for item in logic.find_all_items():
                                if 'addr' in item:
                                    subscribes[index].event_logic['items'].append(item['addr'])
                            # remove duplicates
                            subscribes[index].event_logic['items'] = \
                                list(set(subscribes[index].event_logic['items']))
                            msg['event_logic'] += "Subscribe all items success\n"
                        # unsubscribe
                        else:
                            for x in range(len(subscribes[index].event_logic['items'])):
                                subscribes[index].event_logic['items'].pop()
                            msg['event_items'] += "Unsubscribe all items success\n"
                    # if 'items' is string addr item, then make list with this one item
                    else:
                        args['event_logic']['items'] = [args['event_logic']['items']]
                # list of items
                if isinstance(args['event_logic']['items'], list):
                    if args['command'] == 'subscribe':
                        items = logic.find_all_items()
                        items = [item['addr'] for item in items]
                        flag = False
                        # search for subscribed items in existed items
                        for item in args['event_logic']['items']:
                            if item in items:
                                subscribes[index].event_logic['items'].append(item)
                            else:
                                flag = True
                                msg['event_logic'] += "Item %s not found in logic\n" % (str(item))
                        if not flag:
                            msg['event_logic'] += "Subscribe items success\n"
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
                            msg['event_logic'] += "Subscription items %s not found!\n" % (str(not_found_items))
                        else:
                            msg['event_logic'] += "Unsubscribe success\n"
        # remove last \n
        if len(msg['event_logic']):
            msg['event_logic'] = msg['event_logic'][:-1]
    if 'event_msg' in args:
        if args['command'] == 'subscribe':
            subscribes[index].event_msg = True
            msg['event_msg'] = 'Subscribe success'
        else:
            subscribes[index].event_msg = False
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
                items = logic.find_all_items()
                items = [item['addr'] for item in items]
                # search for subscribed items in existed items
                for item in args['event_items']:
                    if item in items:
                        subscribes[index].event_items.append(item)
                    else:
                        msg['event_items'] += "Item %s not found in logic\n" % (str(item))
                # remove duplicates
                subscribes[index].event_items = \
                    list(set(subscribes[index].event_items))
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
                    for item in logic.find_all_items():
                        if 'addr' in item:
                            subscribes[index].event_items.append(item['addr'])
                    # remove duplicates
                    subscribes[index].event_items = \
                        list(set(subscribes[index].event_items))
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
    # if 'event_statistics' in args:
    #     subscribes[index].event_statistics = args['event_statistics']
    return msg


async def send_message(websocket, message):
    # if connected state
    if websocket.client_state.value == 1:
        await websocket.send_text(message)


def find_index(websocket):
    global subscribes
    for cntr in range(len(subscribes)):
        if subscribes[cntr].websocket == websocket:
            return cntr


async def endpoint(websocket: WebSocket):
    global subscribes, commands, logic
    # добавление нового коннекшна
    subscribes.append(SubscribeWebsocket(websocket))
    await websocket.accept()
    # --------------------------------
    try:
        # обработка сообщений от клиента
        while True:
            data = await websocket.receive_text()
            try:
                data = json.loads(data)
                # check if exists command
                if data['command'] in commands:

                    if data['command'] == 'subscribe' or data['command'] == 'unsubscribe':
                        reply = subscriber(find_index(websocket), data)
                    else:
                        cmd = data['command']
                        data.pop('command')
                        reply = commands[cmd](logic, data)
                else:
                    reply = {'type': 'error', 'message': 'Command not found!'}
            except:
                reply = {'type': 'error', 'message': 'Invalid json!'}
            reply = json.dumps(reply, ensure_ascii=False)
            await websocket.send_text(reply)
    # disconnect client
    except WebSocketDisconnect:
        subscribes.pop(find_index(websocket))


def listener():
    print('Websocket event listener for subscribers started')
    global subscribes, logic
    old_states = dict()
    while True:
        length = len(subscribes)
        for index in range(length):
            if subscribes[index].event_msg:
                pass
            if subscribes[index].event_logic['logic'] and logic.update_flag:
                if logic.logic_update:
                    if 'json' in subscribes[index].event_logic['response_type']:
                        msg = logic.get_dict()
                        response = {'type': 'subscribe-event', 'event_type': "logic_json_update", 'data': msg}
                        asyncio.run(send_message(subscribes[index].websocket, json.dumps(response, ensure_ascii=False)))
                    if 'xml' in subscribes[index].event_logic['response_type']:
                        msg = logic.get_xml().decode('utf-8')
                        response = {'type': 'subscribe-event', 'event_type': "logic_xml_update", 'data': msg}
                        asyncio.run(send_message(subscribes[index].websocket, json.dumps(response, ensure_ascii=False)))
            if subscribes[index].event_logic['items'] and logic.update_flag:
                msg = dict()
                items = logic.find_all_items()
                for addr in subscribes[index].event_logic['items']:
                    if addr in logic.item_update and logic.item_update[addr]:
                        for item in items:
                            if item['addr'] == addr:
                                msg[addr] = item
                                break
                # упаковываем все однотипные ивенты в 1 пакет
                if msg:
                    response = {'type': 'subscribe-event', 'event_type': "logic_item_update",
                                'data': msg}
                    asyncio.run(send_message(subscribes[index].websocket, json.dumps(response, ensure_ascii=False)))
            if subscribes[index].event_items:
                msg = dict()
                for addr in subscribes[index].event_items:
                    if addr in logic.state_items:
                        new_state = logic.state_items[addr]
                        # if new state not equal old state, then send event
                        if addr not in old_states or old_states[addr] != new_state:
                            msg[addr] = new_state.hex(' ')
                # упаковываем все однотипные ивенты в 1 пакет
                if msg:
                    response = {'type': 'subscribe-event', 'event_type': "state_item",
                                'data': msg}
                    asyncio.run(send_message(subscribes[index].websocket, json.dumps(response, ensure_ascii=False)))
            if subscribes[index].event_statistics:
                pass

        # avoid exception: 'dictionary changed size during iteration'
        tmp_state_items = logic.state_items.copy()
        # запоминаем все текущие стейты
        for key, value in tmp_state_items.items():
            old_states[key] = value

        if logic.update_flag:
            # обнуляем флаги обновления логики
            if logic.logic_update:
                logic.logic_update = False
            for key in logic.item_update.keys():
                logic.item_update[key] = False
            logic.update_flag = False

        time.sleep(0.3)


commands = {
    "test": test,
    "get_items": get_items,
    "set_item": set_item,
    "del_item": del_item,
    "get_state": get_state,
    "get_all_states": get_all_states,
    "set_state": set_state,
    "subscribe": subscriber,
    "unsubscribe": subscriber
}
