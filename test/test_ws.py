import json
import unittest

import websocket


class TestWebsocket(unittest.TestCase):
    ws = None

    def setUp(self):
        with open('../config') as f:
            config = json.load(f)
        self.ws = websocket.create_connection("ws://localhost:" + str(config['websocket_port']))
        self.ws.sock.settimeout(1)

    def test_command(self):
        self.ws.send(json.dumps({"command": "test"}))
        response = self.ws.recv()
        self.assertEqual(response, '{"type": "response", "message": "test completed", "data": {}}')
        response = json.loads(response)
        self.assertIs(type(response), dict)

    def __del__(self):
        self.ws.close()
