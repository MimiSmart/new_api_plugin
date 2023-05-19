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

# ---------read logic--------------
logic = Logic(config['logic_path'])
rest.init_logic(logic)
ws.init_logic(logic)
# --------run listener states------
shClient = SHClient("", "", config['key'], config['logic_path'])
shClient.init_logic(logic)
shClient.readFromBlockedSocket = True

threads.append(Thread(target=shClient.listener, name='shclient', daemon=True))

if shClient.run():
    print('Thread [1/4] starting...')
    threads[0].start()
    # shClient.requestAllDevicesState()
    time.sleep(0.1)
else:
    print('Error start SHclient')
# -------run rest & ws-------------
threads.append(Thread(target=server_run, args=[config['local_ip'], config['port']], name='server'))
print('Thread [2/4] starting...')
threads[1].start()

time.sleep(1)

threads.append(Thread(target=ws.listener, name='ws subscribe events', daemon=True))
print('Thread [3/4] starting...')
threads[2].start()


def history_writer(state=None):
    # костыль для свитча. состояние свитча записывается при изменении
    if state:
        pass
    else:
        while True:
            time.sleep(60)
            for item in logic.items.values():
                if item.type != 'switch' and item.state:
                    logic.history_events[item.addr] = item.state  # дописать парсилку
                    item.write_history()


threads.append(Thread(target=history_writer, name='history writer', daemon=True))
print('Thread [4/4] starting...')
threads[3].start()

# проверяем раз в 5 сек живы ли потоки, если нет, то перезапускаем нужный
while True:
    if not threads[0].is_alive():
        try:
            shClient = SHClient("", "", config['key'], config['logic_path'])
            shClient.readFromBlockedSocket = True
            shClient.init_logic(logic)
            if shClient.run():
                threads[0] = Thread(target=shClient.listener, name='shclient', daemon=True)
                print('Thread SHclient starting...')
                threads[0].start()
        except:
            print('Error start SHclient')
    if not threads[1].is_alive():
        try:
            threads[1] = Thread(target=server_run, args=[config['local_ip'], config['port']], name='server')
            print('Thread server starting...')
            threads[1].start()
        except:
            print('Error start WS&REST server')
    if not threads[2].is_alive():
        try:
            threads[2] = Thread(target=ws.listener, name='ws subscribe events', daemon=True)
            print('Thread ws subscribe handler starting...')
            threads[2].start()
        except:
            print('Error start ws subscribe handler')
    if not threads[3].is_alive():
        try:
            threads[3] = Thread(target=history_writer, name='history writer', daemon=True)
            print('Thread history writer starting...')
            threads[3].start()
        except:
            print('Error start history writer')
    # проверка обновилась ли логика
    try:
        logic.update()
    except:
        print("Error logic update")

    time.sleep(1)
