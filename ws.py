import json

import uvicorn
from fastapi import FastAPI, WebSocket

from logic import Logic

logic: Logic = None
app2 = FastAPI()


def test():
    return {
        'type': 'response',
        'message': "test completed"
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


@app2.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        try:
            data = json.loads(data)
            # check if exists command
            if data['command'] in commands:
                reply = commands[data['command']]()
            else:
                reply = {
                    'type': 'error',
                    'message': 'Command not found!'
                }
        except:
            reply = {
                'type': 'error',
                'message': 'Invalid json!'
            }
        reply = json.dumps(reply, ensure_ascii=False)
        await websocket.send_text(reply)


def run(host, port, _logic: Logic):
    global logic
    logic = _logic
    print('WS server run')
    uvicorn.run(app2, host='192.168.1.101', port=8000)
