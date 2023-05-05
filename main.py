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
# config['local_ip'] = '192.168.1.105'  # DEBUG
# ---------read logic--------------
logic = Logic(config['logic_path'])
rest.init_logic(logic)
ws.init_logic(logic)
# --------run listener states------
shClient = SHClient("", "", config['key'], config['logic_path'])
shClient.readFromBlockedSocket = True

threads.append(Thread(target=shClient.listener, args=[logic.state_items], name='shclient', daemon=True))
threads.append(Thread(target=shClient.ping, name='ping SH', daemon=True))

if shClient.run():
    print('Thread [1/4] starting...')
    threads[0].start()
    # shClient.requestAllDevicesState()
    time.sleep(0.1)
    print('Thread [2/4] starting...')
    threads[1].start()
# -------run rest & ws-------------
threads.append(Thread(target=server_run, args=[config['local_ip'], config['port']], name='server'))
print('Thread [3/4] starting...')
threads[2].start()
# rest.run(config['local_ip'], config['port'], logic)

time.sleep(1)

threads.append(Thread(target=ws.listener, name='ws subscribe events', daemon=True))
print('Thread [4/4] starting...')
threads[3].start()

# проверяем раз в 5 сек живы ли потоки, если нет, то перезапускаем нужный
while True:
    if not threads[0].is_alive():
        shClient = SHClient("", "", config['key'], config['logic_path'])
        shClient.readFromBlockedSocket = True
        threads[0] = Thread(target=shClient.listener, args=[logic.state_items], name='shclient', daemon=True)
        threads[0].start()
    if not threads[1].is_alive():
        threads[1] = Thread(target=shClient.ping, name='ping SH', daemon=True)
        threads[1].start()
    if not threads[2].is_alive():
        threads[2] = Thread(target=server_run, args=[config['local_ip'], config['port']], name='server')
        threads[2].start()
    if not threads[3].is_alive():
        threads[3] = Thread(target=ws.listener, name='ws subscribe events', daemon=True)
        threads[3].start()
    time.sleep(5)

# BROKEN PIPE ERROR 32 IN SHCLIENT:
# AF9FB3C0 2023/05/04  7:26:01.602                       SHS: [  !wrn]             shs 2031: Client with duplicated id 2031. Force closing old 'shs 2031'
# AE1F83C0 2023/05/04  7:26:01.611           TCP client recv: [   msg]             shs 2031: Close connection. Recv zero.
# AF9FB3C0 2023/05/04  7:26:01.619               client file: [   msg]             shs 2031: File 'shcxml' was sent (crc32: 0ABE71CD ->> 00000000) 15175.
# AF9FB3C0 2023/05/04  7:26:01.625               TCP XML cmd: [   msg] [2031:  0] command (get-shc) completed successfully.
# AF9FB3C0 2023/05/04  7:26:01.630                TCP client: [   msg]             shs 2031: deleted. Server 'SHS srv' client count: 1
# AF9FB3C0 2023/05/04  7:26:01.817                TCP client: [   msg]             shs 2031: deleted. Server 'SHS srv' client count: 0
