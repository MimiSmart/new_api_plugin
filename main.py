#!/usr/bin/python3.9

# -*- coding: utf-8 -*-
import json
import time
from threading import Thread

import uvicorn

import rest
import tools
# import udp
import ws
from logic import Logic
from shclient import SHClient

config = None
threads = list()


def server_run(host, port):
    rest.app.add_api_websocket_route('/', ws.endpoint)

    # load ws schemas for openapi docs
    with open(tools.home_path + 'websocket_schema.json') as f:
        openapi = rest.app.openapi()
        tmp = json.load(f)
        for key, value in tmp['paths'].items():
            openapi['paths'][key] = value
        for key, value in tmp['schemas'].items():
            openapi['components']['schemas'][key] = value
    uvicorn.run(rest.app, host=host, port=port, ws_per_message_deflate=False)


def main():
    config = tools.read_config()
    keys = tools.read_keys()
    for key in keys:
        if len(key) == 16:
            config['key'] = key
            break

    # ---------read logic--------------
    logic = Logic(config['sh2_path'] + 'logic.xml')

    rest.__init__(logic)
    ws.init_logic(logic)
    # udp.init(logic, config['local_ip'])
    # --------run listener states------
    shClient = SHClient(config['local_ip'], config['udp_port'], config['key'], logic)
    shClient.readFromBlockedSocket = True

    threads.append(Thread(target=shClient.listener, name='shclient listener', daemon=True))
    # threads.append(Thread(target=shClient.sender, name='shclient sender', daemon=True))

    if shClient.run():
        print('Thread shCLient listener starting...')
        threads[0].start()
        time.sleep(0.1)

        # print('Thread shCLient sender starting...')
        # threads[1].start()
        # time.sleep(0.1)
    else:
        print('Error start shClient')
    # -------run rest & ws-------------
    threads.append(Thread(target=server_run, args=[config['local_ip'], config['port']], name='server'))
    print('Thread uvicorn starting...')
    threads[1].start()

    time.sleep(1)

    threads.append(Thread(target=ws.listener, name='ws subscribe events', daemon=True))
    print('Thread ws listener starting...')
    threads[2].start()

    # def history_writer():
    #     while True:
    #         time.sleep(60)
    #         # debug
    #         # time.sleep(15)
    #         for item in logic.items.values():
    #             if item.type != 'switch' and item.state:
    #                 logic.history_events[item.addr] = item.state
    #                 item.write_history()

    # threads.append(Thread(target=history_writer, name='history writer', daemon=True))
    # print('Thread history writer starting...')
    # threads[3].start()

    # threads.append(Thread(target=udp.run, args=[shClient.initClientID], name='udp sniffer', daemon=True))
    # print('Thread udp sniffer starting...')
    # threads[4].start()

    # проверяем раз в 5 сек живы ли потоки, если нет, то перезапускаем нужный
    while True:
        if not threads[0].is_alive():
            try:
                shClient = SHClient(config['local_ip'], config['udp_port'], config['key'], logic)
                shClient.readFromBlockedSocket = True
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
        # if not threads[3].is_alive():
        #     try:
        #         threads[3] = Thread(target=history_writer, name='history writer', daemon=True)
        #         print('Thread history writer starting...')
        #         threads[3].start()
        #     except:
        #         print('Error start history writer')
        # if not threads[4].is_alive():
        #     try:
        #         threads[4] = Thread(target=udp.run, name='udp sniffer', daemon=True)
        #         print('Thread udp sniffer starting...')
        #         threads[4].start()
        #     except:
        #         print('Error start udp sniffer')
        # проверка обновилась ли логика
        try:
            logic.update()
        except:
            print("Error logic update")

        time.sleep(1)


if __name__ == "__main__":
    main()
