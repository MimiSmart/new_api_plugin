import os
import struct
import time
from typing import Union

hst_supported_types = {
    'lamp': 1,
    'script': 1,
    'valve': 1,
    'door-sensor': 1,
    'dimer-lamp': 2,
    'dimmer-lamp': 2,
    'rgb-lamp': 1,
    'valve-heating': 6,
    'conditioner': 6,
    'blinds': 1,
    'gate': 1,
    'jalousie': 1,
    'temperature-sensor': 2,
    'illumination-sensor': 2,
    'motion-sensor': 2,
    'humidity-sensor': 2,
    'voltage-sensor': 2,
    'leak-sensor': 1,
}


class Item:
    addr: str = None
    state: bytes = None
    crc: int = None
    history: list = None
    json_obj: dict = None
    update: bool = None
    # state_timestamp: int = None
    type: str = None
    hst_supported: bool = False

    def __init__(self, addr, crc, update, json_obj):
        self.addr = addr
        self.update = update
        self.crc = crc
        self.json_obj = json_obj
        self.type = self.get_type()
        self.hst_supported = self.type in hst_supported_types.keys()

    def get_type(self):
        if 'type' in self.json_obj:
            return self.json_obj['type']
        else:
            return None

    # .hst structure:
    # [start_timestamp][data_1min,data_2min, ... , data_Nmin]
    # if there was no data for some time - the next data will be written as a new block with a timestamp
    def write_history(self):
        if self.type in hst_supported_types.keys():
            id, subid = self.addr.split(':')
            # make filename
            filename = (4 - len(id)) * '0' + id + '-' + (3 - len(subid)) * '0' + subid + ' ' + self.type + '.hst2'
            if os.path.exists('/home/sh2/exe/new_api_plugin/history/' + filename):
                hst = self.read_history()
                if hst is None:
                    return False
                key = list(hst.keys())
                key.sort()
                key = key[-1]
                with open('/home/sh2/exe/new_api_plugin/history/' + filename, 'ab') as f:
                    # if item wasn`t undefined and cur state is not undefined
                    if hst[key] is not None and self.state[0] != 0xFF:
                        f.write(self.state)
                    else:
                        f.write(0xFF.to_bytes(1, 'little'))
                        f.write(round(time.time()).to_bytes(4, 'little', signed=False))
                        f.write(0xFF.to_bytes(1, 'little'))
                        if self.state[0] != 0xFF:
                            f.write(self.state)
                        else:
                            f.write(b'undefined')
            else:
                with open('/home/sh2/exe/new_api_plugin/history/' + filename, 'wb') as f:
                    f.write(0xFF.to_bytes(1, 'little'))
                    f.write(round(time.time()).to_bytes(4, 'little', signed=False))
                    f.write(0xFF.to_bytes(1, 'little'))
                    if self.state is not None and self.state[0] != 0xFF:
                        f.write(self.state)
                    else:
                        f.write(b'undefined')
        else:
            return False

    # .hst structure:
    # [start_timestamp][data_1min,data_2min, ... , data_Nmin]
    # if there was no data for some time - the next data will be written as a new block with a timestamp
    def read_history(self) -> Union[None, dict]:
        if self.type in hst_supported_types.keys():
            id, subid = self.addr.split(':')
            # make filename
            filename = (4 - len(id)) * '0' + id + '-' + (3 - len(subid)) * '0' + subid + ' ' + self.type + '.hst2'

            hst_bytes = b''
            parsed_hst = dict()

            if os.path.exists('/home/sh2/exe/new_api_plugin/history/' + filename):
                with open('/home/sh2/exe/new_api_plugin/history/' + filename, 'rb') as f:
                    hst_bytes = f.read()
                if hst_bytes:
                    while hst_bytes:
                        _ = hst_bytes[0]
                        timestamp, __ = struct.unpack("IB", hst_bytes[1:6])
                        hst_bytes = hst_bytes[6:]
                        if _ != 0xFF or __ != 0xFF:
                            return None
                        for index in range(len(hst_bytes)):
                            if hst_bytes[index] == 0xFF and index + 5 < len(hst_bytes) and hst_bytes[index + 5] == 0xFF:
                                parsed_hst[timestamp] = hst_bytes[:index]
                                hst_bytes = hst_bytes[index:]
                                break
                        if timestamp not in parsed_hst:
                            parsed_hst[timestamp] = hst_bytes
                            hst_bytes = b''
                        if parsed_hst[timestamp] == b'undefined':
                            # parsed_hst[timestamp] = None
                            if hst_bytes:
                                new_timestamp, __ = struct.unpack("IB", hst_bytes[1:6])
                            else:
                                new_timestamp = round(time.time())
                            times = (new_timestamp - timestamp) // 60
                            parsed_hst[timestamp] = [0xFF for i in range(times)]
                    return parsed_hst
        return None

    def get_history(self, start_time, end_time, scale, wait=False) -> Union[None, list]:
        if wait:
            cntr = 0
            while cntr < 10:
                time.sleep(0.1)
                if self.history:
                    result = self.parse_hst(self.history)
                    self.history = None
                    return result
                cntr += 1
        elif (hst := self.read_history()) and list(hst.keys())[0] <= start_time:
            # парсим историю и определяем с какой временной метки в истории начинать
            keys = list(hst.keys())
            hst = dict(zip(keys, map(self.parse_hst2, hst.values())))
            index = 0
            for key in keys:
                if key < start_time:
                    index += 1
                else:
                    break
            # переводим указатель на start_time состояние и оттуда записываем историю в result
            # пока указатель не дойдет до end_time
            cntr = 0
            result = []
            while keys[index] + cntr * 60 < end_time:
                if keys[index] + cntr * 60 < start_time:
                    cntr += 1
                    continue

                if cntr < len(hst[keys[index]]):
                    result.append(hst[keys[index]][cntr])
                # переходим к поиску в след timestamp`e
                elif index + 1 < len(keys) and keys[index + 1] < end_time:
                    index += 1
                    cntr = 0
                else:
                    break
                cntr += scale
            return result
        return None

    # parse old history, .hst files
    def parse_hst(self, states):
        # switch пропускаю т.к. он стейт присылает только при нажатии и история, собираемая раз в минуту будет бесполезной
        split_states = []
        if not isinstance(states, list):
            states = [states]
        if self.type in ['lamp', 'script', 'valve', 'door-sensor']:
            split_states = [{'state': item & 1} for item in states]
        elif self.type in ['dimmer-lamp', 'dimer-lamp']:
            split_states = [
                {
                    'on': states[index] & 1,
                    'brightness': round(int((states[index + 1]) * 100 / 255.0), 1)
                }
                for index in range(0, len(states), 2)
            ]
        elif self.type == 'rgb-lamp':
            # rgb in old history save only value (brightness)
            split_states = [
                {'on': item > 0,
                 'value': item if item > 0 else 0
                 }
                for item in states]
        elif self.type == 'valve-heating':
            split_states = [
                # opt0 - видимо вкл/выкл, 0xFA на вкл
                # opt1 - дробная сенсора
                # opt2 - целая сенсора
                # opt3 - дробная установленная
                # opt4 - целая установленная
                {
                    'on': 1 if states[index] == 0xFA else 0,
                    'set_temperature': round(states[index + 4] + (states[index + 3] / 255.0), 2),
                    'sensor_temperature': round(states[index + 2] + (states[index + 1] / 255.0), 2)
                }
                for index in range(0, len(states), 5)]
        elif self.type in 'conditioner':
            split_states = [{'temperature': states[i]} for i in range(4, len(states), 5)]
        elif self.type in ['jalousie', 'blinds', 'gate']:
            split_states = []
            for item in states:
                tmp = {'state': None}
                if not item:
                    tmp['state'] = 'close'
                elif item == 0x7D:
                    tmp['state'] = 'half opened'
                elif item == 0xFA:
                    tmp['state'] = 'opened'
                else:
                    tmp['state'] = 'undefined'
                split_states.append(tmp)
        elif self.type in ['temperature-sensor', 'motion-sensor', 'illumination-sensor', 'humidity-sensor']:
            split_states = [{'state': round(states[index + 1] + (states[index] / 255.0), 2)} for index in
                            range(0, len(states), 2)]
        elif self.type == 'leak-sensor':
            split_states = [{'state': item} for item in states]
        return split_states

    # parse new history, .hst2 files
    def parse_hst2(self, states):
        # switch пропускаю т.к. он стейт присылает только при нажатии и история, собираемая раз в минуту будет бесполезной
        split_states = []
        if states is None: return None
        states = [x for x in states]
        if self.type in ['lamp', 'script', 'valve', 'door-sensor']:
            split_states = [{'state': item & 1} for item in states]
        elif self.type in ['dimmer-lamp', 'dimer-lamp']:
            split_states = [
                {
                    'on': states[index] & 1,
                    'brightness': round(int((states[index + 1]) * 100 / 255.0), 1)
                }
                for index in range(0, len(states), 2)
            ]
        elif self.type == 'rgb-lamp':
            split_states = [
                {
                    'on': states[index] & 1,
                    'value': round(int((states[index + 1]) * 100 / 255.0), 1),
                    'saturation': round(int((states[index + 2]) * 100 / 255.0), 1),
                    'hue': round(int((states[index + 3]) * 100 / 255.0), 1),
                }
                for index in range(0, len(states), 4)
            ]
        elif self.type == 'valve-heating':
            # opt0 - видимо вкл/выкл, 0xFA на вкл
            # opt1 - дробная установленная
            # opt2 - целая установленная
            # opt3 - дробная сенсора
            # opt4 - целая сенсора
            # opt5 - номер автоматизации
            split_states = [
                {
                    'on': 1 if states[index] == 0xFA else 0,
                    'set_temperature': round(states[index + 2] + (states[index + 1] / 255.0), 2),
                    'sensor_temperature': round(states[index + 4] + (states[index + 3] / 255.0), 2),
                    'num_automation': states[index + 5]
                }
                for index in range(0, len(states), 6)]
        elif self.type in 'conditioner':
            split_states = [
                {
                    'on': states[index] & 1,
                    'mode': states[index] >> 4,
                    'temperature': states[index + 1],  # нужно добавить t-min
                    'vane-hor': states[index + 3] & 0x0F,
                    'vane-ver': states[index + 3] >> 4,
                    'fan': states[index + 4] & 0x0F
                }
                for index in range(0, len(states), 6)
            ]
        elif self.type in ['jalousie', 'blinds', 'gate']:
            split_states = [{'state': item} for item in states]
        elif self.type in ['temperature-sensor', 'motion-sensor', 'illumination-sensor', 'humidity-sensor']:
            split_states = [{'state': round(states[index + 1] + (states[index] / 255.0), 2)} for index in
                            range(0, len(states), 2)]
        elif self.type == 'leak-sensor':
            split_states = [{'state': item} for item in states]
        return split_states
