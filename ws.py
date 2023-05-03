import asyncio
import json
import time

from fastapi import WebSocket

from logic import Logic


def test(logic: Logic, args):
    return {
        'type': 'response',
        'message': "test completed"
    }


def get_items(logic: Logic, args):
    return {
        'type': 'response',
        'data': logic.get_json()
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


class SubscribeWebsocket:
    websocket: WebSocket
    event_logic: bool
    event_items: list
    event_statistics: list
    event_msg: bool

    def __init__(self, websocket: WebSocket,
                 event_logic: bool = False,
                 event_items: list = None,
                 event_statistics: list = None,
                 event_msg: bool = False):
        self.websocket = websocket
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


def subscriber(logic: Logic, subscribes, index, args):
    msg = {'type': 'response'}

    if 'event_logic' in args:
        if args['command'] == 'subscribe':
            subscribes[index].event_logic = True
            msg['event_logic'] = 'Subscribe success'
        else:
            subscribes[index].event_logic = False
            msg['event_logic'] = 'Unsubscribe success'
    if 'event_msg' in args:
        if args['command'] == 'subscribe':
            subscribes[index].event_msg = True
            msg['event_msg'] = 'Subscribe success'
        else:
            subscribes[index].event_msg = False
            msg['event_msg'] = 'Unsubscribe success'
    if 'event_items' in args:
        msg['event_items'] = ''
        if isinstance(args['event_items'], str) and args['event_items'] != 'all':
            args['event_items'] = [args['event_items']]
        if isinstance(args['event_items'], list):
            if args['command'] == 'subscribe':
                items = logic.find_all_items(logic.obj_logic)
                items = [item['addr'] for item in items]
                for item in args['event_items']:
                    if item in items:
                        subscribes[index].event_items.append(item)
                    # добавить проверку существует ли итем в логике
                # remove duplicates
                subscribes[index].event_items = \
                    list(set(subscribes[index].event_items))
                msg['event_items'] += "Subscribe success\n"
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

        elif isinstance(args['event_items'], str):
            if args['event_items'] == 'all':
                if args['command'] == 'subscribe':
                    for item in logic.find_all_items(logic.obj_logic):
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
                msg['event_items'] += "'event_items' supported only 'all' or list of items\n"

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


def event_listener(logic: Logic, subscribes):
    old_states = dict()
    while True:
        length = len(subscribes)
        for index in range(length):
            if subscribes[index].event_msg:
                pass
            if subscribes[index].event_logic:
                pass
            if subscribes[index].event_items:
                msg = dict()
                for addr in subscribes[index].event_items:
                    if addr in logic.state_items:
                        new_state = logic.state_items[addr]['state']
                        # if new state not equal old state, then send event
                        if addr not in old_states or old_states[addr] != new_state:
                            msg[addr] = new_state
                # упаковываем все однотипные ивенты в 1 пакет
                if msg:
                    response = {'type': 'subscribe-event', 'event_type': "state_item",
                                'events': msg}
                    asyncio.run(send_message(subscribes[index].websocket, json.dumps(response)))
            if subscribes[index].event_statistics:
                pass

        # запоминаем все текущие стейты
        for key, value in logic.state_items.items():
            old_states[key] = value['state']

        time.sleep(1)


commands = {
    "test": test,
    "get_items": get_items,
    "set_item": set_item,
    "del_item": del_item,
    "get_state": get_state,
    "get_all_states": get_all_states,
    "subscribe": subscriber,
    "unsubscribe": subscriber
}
