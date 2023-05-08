#!/usr/bin/python3.9

# -*- coding: utf-8 -*-
import json
import time
from threading import Thread

import uvicorn

import rest
import ws
from logic import Logic
from shclient import SHClient

config = None
threads = list()

home_path = '/home/sh2/exe/new_api_plugin/'  # RELEASE


# home_path = './'  # DEBUG


def server_run(host, port):
    rest.app.add_api_websocket_route('/', ws.endpoint)

    # load ws schemas for openapi docs
    with open(home_path + 'websocket_schema.json') as f:
        openapi = rest.app.openapi()
        tmp = json.load(f)
        for key, value in tmp['paths'].items():
            openapi['paths'][key] = value
        for key, value in tmp['schemas'].items():
            openapi['components']['schemas'][key] = value

    uvicorn.run(rest.app, host=host, port=port)


# ---------read config-------------
with open(home_path + 'config') as f:
    config = json.load(f)

# config['logic_path'] = 'logic.xml'  # DEBUG
# config['local_ip'] = '192.168.1.106'  # DEBUG
# ---------read logic--------------
logic = Logic(config['logic_path'])
rest.init_logic(logic)
ws.init_logic(logic)
# --------run listener states------
shClient = SHClient("", "", config['key'], config['logic_path'])
shClient.readFromBlockedSocket = True

threads.append(Thread(target=shClient.listener, args=[logic.state_items], name='shclient', daemon=True))

if shClient.run():
    print('Thread [1/3] starting...')
    threads[0].start()
    # shClient.requestAllDevicesState()
    time.sleep(0.1)
else:
    print('Error start SHclient')
# -------run rest & ws-------------
threads.append(Thread(target=server_run, args=[config['local_ip'], config['port']], name='server'))
print('Thread [2/3] starting...')
threads[1].start()
# rest.run(config['local_ip'], config['port'], logic)

time.sleep(1)

threads.append(Thread(target=ws.listener, name='ws subscribe events', daemon=True))
print('Thread [3/3] starting...')
threads[2].start()

# проверяем раз в 5 сек живы ли потоки, если нет, то перезапускаем нужный
while True:
    if not threads[0].is_alive():
        shClient = SHClient("", "", config['key'], config['logic_path'])
        shClient.readFromBlockedSocket = True
        if shClient.run():
            threads[0] = Thread(target=shClient.listener, args=[logic.state_items], name='shclient', daemon=True)
            threads[0].start()
        else:
            print('Error start SHclient')
    if not threads[1].is_alive():
        threads[1] = Thread(target=server_run, args=[config['local_ip'], config['port']], name='server')
        threads[1].start()
    if not threads[2].is_alive():
        threads[2] = Thread(target=ws.listener, name='ws subscribe events', daemon=True)
        threads[2].start()

    # проверка обновилась ли логика
    logic.update()

    time.sleep(5)
