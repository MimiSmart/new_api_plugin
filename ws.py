import asyncio
import json

import websockets

from logic import Logic

logic : Logic = None

def test():
    return {
        'type': 'response',
        'message': "test completed",
        'data': {}
    }

def get_items():
    return {
        'type': 'response',
        'data': logic.get_json()
    }


commands = {
    "test": test,
    "get_items": get_items
}


async def handler(websocket, path):
    data = await websocket.recv()
    print(data)
    try:
        data = json.loads(data)
        # check if exists command
        if data['command'] in commands:
            reply = commands[data['command']]()
        else:
            reply = {
                'type': 'error',
                'message': 'Command not found!',
                'data': {}
            }
    except:
        reply = {
            'type': 'error',
            'message': 'Invalid json!',
            'data': {}
        }
    reply = json.dumps(reply,ensure_ascii=False)
    await websocket.send(reply)


def run(port, _logic : Logic):
    global logic
    logic = _logic
    start_server = websockets.serve(handler, "localhost", port)
    ws_loop = asyncio.get_event_loop()

    ws_loop.run_until_complete(start_server)
    ws_loop.run_forever()
