#!/usr/bin/python3.9

# -*- coding: utf-8 -*-
import json
from threading import Thread

import rest
import ws
from logic import Logic

config = None

with open('/home/sh2/exe/new_api_plugin/config') as f:
# with open('config') as f:
    config = json.load(f)

# config['logic_path'] = 'logic.xml'  # DEBUG
# config['local_ip'] = '192.168.1.101'  # DEBUG

logic = Logic(config['logic_path'])

rest_runner = Thread(target=rest.run, args=[config['local_ip'], config['rest_port'], logic])
rest_runner.start()
ws.run(config['local_ip'], config['websocket_port'], logic)
