#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio
import json
from threading import Thread

import websockets

import rest
import ws

rest_runner = Thread(target=rest.run)
rest_runner.start()
ws.run()
