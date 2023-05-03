#!/usr/bin/python3.9

# -*- coding: utf-8 -*-
import json
from threading import Thread

import rest
from logic import Logic
from shclient import SHClient

config = None

home_path = '/home/sh2/exe/new_api_plugin/'  # RELEASE
# home_path = './'  # DEBUG

# ---------read config-------------
with open(home_path + 'config') as f:
    config = json.load(f)

# config['logic_path'] = 'logic.xml'  # DEBUG
# config['local_ip'] = '192.168.1.106'  # DEBUG
# ---------read logic--------------
logic = Logic(config['logic_path'])

# --------run listener states------
shClient = SHClient("", "", config['key'], config['logic_path'])
shClient.readFromBlockedSocket = True
if shClient.run():
    shClient_thread = Thread(target=shClient.listener, args=[logic.state_items], name='shclient')
    shClient_thread.start()
    shClient.requestAllDevicesState()

# -------run rest & ws-------------
rest.run(config['local_ip'], config['port'], logic)
# import ws
#
# response = ws.set_item(logic, {"type": "write",
#                                "tag": "item",
#                                "area": "Setup9",
#                                "data": {"name": "test item", "addr": "588:8"}})
# logic.set_item('append', 'item', 'Setup9', {'name': 'Temperature', 'addr': '588:8'})
# logic.set_item('remove', 'item', 'Setup9', {'addr': '588:8', 'name': ''})
# response = logic.set_item('write', 'item', 'Гостиная', {'name':'test item','test': 'test', 'addr': '588:8'})
# areas = logic.find_all_items(logic.obj_logic,'area')
# items = logic.find_all_items(logic.obj_logic, 'item')
