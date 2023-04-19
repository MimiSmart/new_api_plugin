#!/usr/bin/python3
# -*- coding: utf-8 -*-
import json
from threading import Thread

import rest
import ws
from logic import Logic

config = None

with open('config') as f:
    config = json.load(f)

config['logic_path'] = config['logic_path_debug'] #DEBUG

logic = Logic(config['logic_path'])

rest_runner = Thread(target=rest.run, args=[config['rest_port'], logic])
rest_runner.start()
ws.run(config['websocket_port'], logic)

# print(logic.checksum())
# items = logic._find_all_items(logic.obj_logic)
# logic.update()
