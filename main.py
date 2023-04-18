#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio
import json
from threading import Thread

import websockets

import rest


# WS сервер
def test():
    return {
        'type': 'response',
        'body': {
            'message': "test completed"
        }
    }


commands = {
    "test": test
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
                'body': {
                    'message': 'Command not found!'
                }
            }
    except:
        reply = {
            'type': 'error',
            'body': {
                'message': 'Invalid json!'
            }
        }
    reply = json.dumps(reply)
    await websocket.send(reply)


start_server = websockets.serve(handler, "localhost", 8000)
ws_loop = asyncio.get_event_loop()

rest_runner = Thread(target=rest.run)
rest_runner.start()

ws_loop.run_until_complete(start_server)
ws_loop.run_forever()
