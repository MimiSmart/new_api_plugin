import os
import time
from typing import Union

import more_itertools

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
    'switch': 1
}

hst_path = '/home/sh2/exe/new_api_plugin/history/'

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
                    except:
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
                        except:
                            pass
                # if file hst not found
                else:
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
        diff = end - start
        steps = int(diff / (scale * 60))
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
            index = 0
            # переводим указатель на start_time состояние и оттуда записываем историю в result
            # пока указатель не дойдет до end_time
            cntr = 0
            result = []
            while keys[index] + cntr * 60 < end_time:
                # skip some iter
                if keys[index] + cntr * 60 < start_time:
                    if not cntr:
                        cntr = round((start_time - keys[index]) / 60)
                    else:
                        cntr += 1
                    continue

                #заполняем результат нужными сегментами, с шагом scale
                if cntr < len(hst[keys[index]]):
                    result.extend(hst[keys[index]][cntr::scale])
                    cntr = len(hst[keys[index]])
                # переходим к поиску в след timestamp`e
                elif index + 1 < len(keys) and keys[index + 1] < end_time:
                    index += 1
                    cntr = 0
                else:
                    break
            result = self.add_timestamp_hst(result, start_time, end_time, scale)
            return result
        return None

    # parse old history, .hst files
    def parse_hst(self, states):
        # switch пропускаю т.к. он стейт присылает только при нажатии и история, собираемая раз в минуту будет бесполезной
        split_states = []
        if not isinstance(states, list):
            states = [states]
        if self.type in ['lamp', 'script', 'valve', 'door-sensor']:
            split_states = [{'state': (item & 1).to_bytes(1, 'big').hex(' ')} for item in states]
        elif self.type in ['dimmer-lamp', 'dimer-lamp']:
            split_states = [{'state': bytes(states[index:index + 2]).hex(' ')}
                            for index in range(0, len(states), 2)]
            # split_states = [
            #     {
            #         'on': states[index] & 1,
            #         'brightness': round(int((states[index + 1]) * 100 / 255.0), 1)
            #     }
            #     for index in range(0, len(states), 2)
            # ]
        elif self.type == 'rgb-lamp':
            # rgb in old history save only value (brightness)
            split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
            # split_states = [
            #     {'on': item > 0,
            #      'value': item if item > 0 else 0
            #      }
            #     for item in states]
        elif self.type == 'valve-heating':
            split_states = [{'state': bytes(states[index:index + 5]).hex(' ')}
                            for index in range(0, len(states), 5)]
            # split_states = [
            #     # opt0 - видимо вкл/выкл, 0xFA на вкл
            #     # opt1 - дробная сенсора
            #     # opt2 - целая сенсора
            #     # opt3 - дробная установленная
            #     # opt4 - целая установленная
            #     {
            #         'on': 1 if states[index] == 0xFA else 0,
            #         'set_temperature': round(states[index + 4] + (states[index + 3] / 255.0), 2),
            #         'sensor_temperature': round(states[index + 2] + (states[index + 1] / 255.0), 2)
            #     }
            #     for index in range(0, len(states), 5)]
        elif self.type in 'conditioner':
            split_states = [{'state': states[i].to_bytes(1, 'big').hex(' ')} for i in range(4, len(states), 5)]
            # split_states = [{'temperature': states[i]} for i in range(4, len(states), 5)]
        elif self.type in ['jalousie', 'blinds', 'gate']:
            split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
            # split_states = []
            # for item in states:
            #     tmp = {'state': None}
            #     if not item:
            #         tmp['state'] = 'close'
            #     elif item == 0x7D:
            #         tmp['state'] = 'half opened'
            #     elif item == 0xFA:
            #         tmp['state'] = 'opened'
            #     else:
            #         tmp['state'] = 'undefined'
            #     split_states.append(tmp)
        elif self.type in ['temperature-sensor', 'motion-sensor', 'illumination-sensor', 'humidity-sensor']:
            split_states = [{'state': bytes(states[index:index + 2]).hex(' ')} for index in
                            range(0, len(states), 2)]
            # split_states = [{'state': round(states[index + 1] + (states[index] / 255.0), 2)} for index in
            #                 range(0, len(states), 2)]
        elif self.type == 'leak-sensor':
            split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
            # split_states = [{'state': item} for item in states]
        return split_states

    # parse new history, .hst2 files
    def parse_hst2(self, states):
        # switch пропускаю т.к. он стейт присылает только при нажатии и история, собираемая раз в минуту будет бесполезной
        split_states = []
        if states is None: return None
        states = [x for x in states]

        # undefined
        if states[0] == 0xFF:
            split_states = [{'state': 'undefined'} for item in states]
            return split_states

        if self.type in ['lamp', 'script', 'valve', 'door-sensor']:
            split_states = [{'state': (item & 1).to_bytes(1, 'big').hex(' ')} for item in states]
            # split_states = [{'state': item & 1} for item in states]
        elif self.type in ['dimmer-lamp', 'dimer-lamp']:
            split_states = [{'state': bytes(states[index:index + 2]).hex(' ')}
                            for index in range(0, len(states), 2)]
            # split_states = [
            #     {
            #         'on': states[index] & 1,
            #         'brightness': round(int((states[index + 1]) * 100 / 255.0), 1)
            #     }
            #     for index in range(0, len(states), 2)
            # ]
        elif self.type == 'rgb-lamp':
            split_states = [{'state': bytes(states[index:index + 4]).hex(' ')}
                            for index in range(0, len(states), 4)]
            # split_states = [
            #     {
            #         'on': states[index] & 1,
            #         'value': round(int((states[index + 1]) * 100 / 255.0), 1),
            #         'saturation': round(int((states[index + 2]) * 100 / 255.0), 1),
            #         'hue': round(int((states[index + 3]) * 100 / 255.0), 1),
            #     }
            #     for index in range(0, len(states), 4)
            # ]
        elif self.type == 'valve-heating':
            # opt0 - старшие 4 бита - номер автоматизации, младшие - вкл/выкл
            # opt1 - дробная установленная
            # opt2 - целая установленная
            # opt3 - дробная сенсора
            # opt4 - целая сенсора
            # opt5 - 0xFF, 0xFA или 0

            split_states = [{'state': bytes(states[index:index + 6]).hex(' ')}
                            for index in range(0, len(states), 6)]

            # split_states = [
            #     {
            #         'on': states[index] & 1,
            #         'set_temperature': round(states[index + 2] + (states[index + 1] / 255.0), 2),
            #         'sensor_temperature': round(states[index + 4] + (states[index + 3] / 255.0), 2),
            #         'num_automation': states[index] >> 4 if not states[index + 5] else states[index + 5]
            #     }
            #     for index in range(0, len(states), 6)]
        elif self.type in 'conditioner':
            split_states = [{'state': bytes(states[index:index + 6]).hex(' ')}
                            for index in range(0, len(states), 6)]

            # split_states = [
            #     {
            #         'on': states[index] & 1,
            #         'mode': states[index] >> 4,
            #         'temperature': states[index + 1],  # нужно добавить t-min
            #         'vane-hor': states[index + 3] & 0x0F,
            #         'vane-ver': states[index + 3] >> 4,
            #         'fan': states[index + 4] & 0x0F
            #     }
            #     for index in range(0, len(states), 6)
            # ]
        elif self.type in ['jalousie', 'blinds', 'gate']:
            split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
            # split_states = [{'state': item} for item in states]
        elif self.type in ['temperature-sensor', 'motion-sensor', 'illumination-sensor', 'humidity-sensor']:
            split_states = [{'state': bytes(states[index:index + 2]).hex(' ')}
                            for index in range(0, len(states), 2)]
            # split_states = [{'state': round(states[index + 1] + (states[index] / 255.0), 2)} for index in
            #                 range(0, len(states), 2)]
        elif self.type == 'leak-sensor':
            split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
            # split_states = [{'state': item} for item in states]
        return split_states

    def get_state(self):
        try:
            return self.state.hex(' ')
        except:
            return None

    def set_state(self, state):
        state = self.presetter(state)

        if self.size_state > 0 and len(state) <= self.size_state:
            if self.state is not None:
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
        state = list(state)
        if self.type in ['lamp', 'valve-heating', 'valve']:
            # если 0xFF - изменить состояние на противоположное
            if state[0] == 0xFF:
                state[0] = self.state[0] ^ 1 if self.state[0] & 1 else self.state[0] | 1
        elif self.type in ['dimer-lamp', 'dimmer-lamp']:
            # если диммеру устанавливается статус с временем изменения яркости - игнорим время
            if len(state) == 3:
                state = state[:2]
            # если 0xFF - изменить состояние на противоположное
            if state[0] == 0xFF:
                state = self.state[0] ^ 1 if self.state[0] & 1 else self.state[0] | 1
            # если 0xFE - не изменять состояние
            for index in range(len(state)):
                if state[index] == 0xFE:
                    state[index] = self.state[index]
        elif self.type == 'rgb-lamp':
            # если rgb устанавливается статус с временем изменения яркости - игнорим время
            if len(state) == 5:
                state = state[:4]
            # если 0xFF - изменить состояние на противоположное
            if state[0] == 0xFF:
                state[0] = self.state[0] ^ 1 if self.state[0] & 1 else self.state[0] | 1

            # если 0xFE - не изменять состояние
            for index in range(len(state)):
                if state[index] == 0xFE:
                    state[index] = self.state[index]
        elif self.type in ['jalousie', 'gate', 'blinds']:
            # на жалюзи нужно получать данные от сервера, т.к. непонятно когда в каком положении они будут

            # если на жалюзи устанавливается статус с временем хода - игнорим время
            if len(state) == 2:
                state = state[0]
            # если 0xFF - изменить состояние на противоположное
            if state[0] == 0xFF:
                if self.state[0] in [0, 2]:
                    state[0] = 3
                elif self.state[0] in [1, 3]:
                    state[0] = 2
                # state[0] = self.state[0] ^ 1 if self.state[0] & 1 else self.state[0] | 1
        state = bytes(state)
        return state
