import os
import time
from typing import Union
import traceback
import more_itertools

from items import *

# size states in old history:
# 'lamp': 1,
# 'script': 1,
# 'valve': 1,
# 'door-sensor': 1,
# 'dimer-lamp': 2,
# 'dimmer-lamp': 2,
# 'rgb-lamp': 1,
# 'valve-heating': 6,
# 'conditioner': 6,
# 'blinds': 1,
# 'gate': 1,
# 'jalousie': 1,
# 'temperature-sensor': 2,
# 'illumination-sensor': 2,
# 'motion-sensor': 2,
# 'humidity-sensor': 2,
# 'voltage-sensor': 2,
# 'leak-sensor': 1,
# 'switch': 1
hst_supported_types = [
    'lamp',
    'script'
    'valve',
    'door-sensor',
    'dimer-lamp',
    'dimmer-lamp',
    'rgb-lamp',
    'valve-heating',
    'conditioner',
    'blinds',
    'gate',
    'jalousie',
    'temperature-sensor',
    'illumination-sensor',
    'motion-sensor',
    'humidity-sensor',
    'voltage-sensor',
    'leak-sensor',
    'switch'
]
size_states = {
    'lamp': 1,
    'script': 1,
    'valve': 1,
    'door-sensor': 1,
    'dimer-lamp': 2,
    'dimmer-lamp': 2,
    'rgb-lamp': 4,
    'valve-heating': 5,
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
    'switch': 1
}

hst_path = '/home/sh2/exe/new_api_plugin/history/'

item = {
    'lamp': lamp,
    'script': lamp,
    'valve': lamp,
    'door-sensor': lamp,
    'dimmer-lamp': dimmer,
    'dimer-lamp': dimmer,
    'rgb-lamp': rgb,
    'valve-heating': heating,
    'conditioner': conditioner,
    'jalousie': blinds,
    'blinds': blinds,
    'gate': blinds,
    'temperature-sensor': sensor,
    'motion-sensor': sensor,
    'illumination-sensor': sensor,
    'humidity-sensor': sensor,
    'leak-sensor': leak,
}


class Item:
    addr: str = None
    state: bytes = None
    size_state: int = None
    crc: int = None
    history: list = None
    json_obj: dict = None
    update: bool = None
    # state_timestamp: int = None
    type: str = None
    hst_supported: bool = False
    filename: str = ''

    def __init__(self, addr, crc, update, json_obj):
        self.addr = addr
        self.update = update
        self.crc = crc
        self.json_obj = json_obj
        self.type = self.get_type()
        self.hst_supported = self.type in hst_supported_types
        # если размер прописан - берем его, иначе неограниченный
        self.size_state = size_states[self.type] if self.type in size_states.keys() else 0
        # make filename
        id, subid = addr.split(':')
        self.filename = (4 - len(id)) * '0' + id + '-' + (3 - len(subid)) * '0' + subid + ' ' + self.type + '.hst2'

    def get_type(self):
        if 'type' in self.json_obj:
            return self.json_obj['type']
        else:
            return None

    # .hst structure:
    # [start_timestamp][data_1min,data_2min, ... , data_Nmin]
    # if there was no data for some time - the next data will be written as a new block with a timestamp
    def write_history(self):
        global hst_path
        if self.type in hst_supported_types:
            id, subid = self.addr.split(':')

            if self.type == 'switch':
                if not os.path.exists(hst_path + self.filename):
                    open(hst_path + self.filename, 'wb').close()
                with open(hst_path + self.filename, 'ab') as f:
                    if self.state is not None:
                        f.write(0xFF.to_bytes(1, 'little'))
                        f.write(round(time.time()).to_bytes(4, 'little', signed=False))
                        f.write(0xFF.to_bytes(1, 'little'))
                        f.write(self.state)
            else:
                if os.path.exists(hst_path + self.filename):

                    hst = self.read_history()
                    if hst is None:
                        return False
                    key = list(hst.keys())
                    key.sort()
                    key = key[-1]

                    # если в последнем timestamp записей меньше чем должно быть к текущему моменту
                    # значит апи отключали, просто забиваем undef
                    diff = int(time.time() - (key + (len(hst[key]) * 60 / self.size_state)))
                    try:
                        if diff > 60 and hst[key][0] != 0xFF:
                            # cntr = int(diff / 60)
                            with open(hst_path + self.filename, 'ab') as f:
                                f.write(0xFF.to_bytes(1, 'little'))
                                new_timestamp = round(key + (len(hst[key]) * 60 / self.size_state) + 60)
                                f.write(new_timestamp.to_bytes(4, 'little', signed=False))
                                f.write(0xFF.to_bytes(1, 'little'))
                                f.write(b'undefined')
                            hst = self.read_history()
                            if hst is None:
                                return False
                            key = list(hst.keys())
                            key.sort()
                            key = key[-1]
                    except Exception as ex:
                        print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
                        pass
                    with open(hst_path + self.filename, 'ab') as f:
                        try:
                            # if item wasn`t undefined and cur state is not undefined
                            if hst[key][0] != 0xFF and self.state is not None and self.state[0] != 0xFF:
                                f.write(self.state)
                            # if item was undefined and cur state is undefined - skip
                            elif hst[key][0] == 0xFF and self.state is not None and self.state[0] == 0xFF:
                                pass
                            # new timestamp
                            else:
                                f.write(0xFF.to_bytes(1, 'little'))
                                f.write(round(time.time()).to_bytes(4, 'little', signed=False))
                                f.write(0xFF.to_bytes(1, 'little'))
                                if self.state[0] != 0xFF:
                                    f.write(self.state)
                                else:
                                    f.write(b'undefined')
                        except Exception as ex:
                            print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
                            pass
                # if file hst not found
                else:
                    os.makedirs(hst_path, exist_ok=True)
                    with open(hst_path + self.filename, 'wb') as f:
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
        global hst_path
        if self.type in hst_supported_types:
            hst_bytes = b''

            if os.path.exists(hst_path + self.filename):
                # read history
                with open(hst_path + self.filename, 'rb') as f:
                    hst_bytes = f.read()

                if hst_bytes:
                    tmp = list(more_itertools.split_at(hst_bytes, lambda x: x == 0xFF))
                    while ([] in tmp):
                        tmp.remove([])
                    # все четные индексы - метки
                    timestamps = [int.from_bytes(bytes(item), 'little') for item in tmp[::2]]
                    # все нечетные индексы - сегменты истории
                    data_segments = [bytes(item) for item in tmp[1::2]]

                    # parse undefined state
                    # for timestamp, segment in parsed_hst.values():
                    cntr = 0
                    for item in data_segments:
                        if item == b'undefined':
                            try:
                                new_timestamp = timestamps[cntr + 1]
                            except:
                                new_timestamp = round(time.time())
                            times = (new_timestamp - timestamps[cntr]) // 60
                            data_segments[cntr] = [0xFF for i in range(times)]
                        cntr += 1
                    # убираем пустые
                    while ([] in data_segments):
                        data_segments.remove([])

                    parsed_hst = dict(zip(timestamps, data_segments))
                    return parsed_hst
        return None

    def add_timestamp_hst(self, hst, start, end, scale):
        if not len(hst): return hst
        cntr = 0
        # diff = end - start
        # steps = int(diff / (scale * 60))
        stepDiff = scale * 60
        for item in hst:
            item['timestamp'] = int(start + (stepDiff * cntr))
            cntr += 1
        return hst

    def get_history(self, start_time, end_time, scale, wait=False) -> Union[None, list]:
        if wait:
            cntr = 0
            while cntr < 10:
                time.sleep(0.1)
                if self.history:
                    result = self.parse_hst(self.history)
                    result = self.add_timestamp_hst(result, start_time, end_time, scale)
                    self.history = None
                    return result
                cntr += 1
        elif (hst := self.read_history()) and int(list(hst.keys())[0]) <= int(start_time):
            # определяем с какой временной метки в истории начинать
            keys = list(hst.keys())
            hst = dict(zip(keys, map(self.parse_hst2, hst.values())))
            tmp = []
            for value in hst.values():
                tmp.extend(value)
            hst = tmp
            # переводим указатель на start_time состояние и оттуда записываем историю в result
            # пока указатель не дойдет до end_time
            start = (start_time - keys[0]) // 60
            steps = (end_time - start_time) // 60
            end = start + steps
            result = self.add_timestamp_hst(hst[start:end:scale], start_time, end_time, scale)
            return result
        return None

    # parse old history, .hst files
    def parse_hst(self, states):
        global item
        # switch пропускаю т.к. он стейт присылает только при нажатии и история, собираемая раз в минуту будет бесполезной
        if not isinstance(states, list):
            states = [states]
        split_states = item[self.type].parse_hst(states)
        return split_states

    # parse new history, .hst2 files
    def parse_hst2(self, states):
        global item
        # switch пропускаю т.к. он стейт присылает только при нажатии и история, собираемая раз в минуту будет бесполезной
        split_states = []
        if states is None: return None
        states = [x for x in states]

        # undefined
        if states[0] == 0xFF:
            split_states = [{'state': 'undefined'} for item in states]
            return split_states

        split_states = item[self.type].parse_hst2(states)
        return split_states

    def get_state(self):
        try:
            if self.type == 'valve-heating':
                # когда режим always-off / manual - температуру не показывает
                return bytes([self.state[0], self.state[2]]).hex(' ')
            else:
                return self.state.hex(' ')
        except:
            return None

    def set_state(self, state):
        state = self.presetter(state)

        if self.size_state > 0 and len(state) <= self.size_state:
            if self.state is not None:
                # если до этого статус был длиннее - остальное оставляем как было
                self.state = state + self.state[len(state):]
            else:
                self.state = state
                for x in range(self.size_state - len(state)):
                    self.state += b'\0'
        elif self.size_state == 0:
            self.state = state
        else:
            print(
                f"Item set-state func.: Error set state! Addr:{self.addr}; Type: {self.type}; Size state: {self.size_state}; Settable state:{state}")

    def presetter(self, state):
        global item
        if state is None:
            return None
        else:
            if self.type in item.keys():
                state = list(state)
                state = item[self.type].preset(self, state)
                state = bytes(state)
            return state
