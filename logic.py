# -*- coding: utf-8 -*-
import json
import subprocess
import time
from collections import defaultdict
from typing import Dict
from xml.etree import cElementTree as ET

import tools
from item import Item
from mytimer import timeit


class Logic:
    path_logic: str = ""

    _header: bytes = b""
    xml_logic: bytes = b""
    obj_logic = None

    crc16: int = 0
    logic_update: bool = False

    items: Dict[str, Item] = dict()

    set_queue = list()
    # в history_requests закидываются запросы на историю к серверу через shclient
    history_requests = dict()
    # в history_events закидываются стейты, которые были дописаны в историю, которые нужно отправить по подписке
    history_events = dict()
    # сюда закидываем запросы на пуши
    push_requests = list()
    # сюда закидываются пуши, которые пришли от сервера, и потом отправляются подписчикам
    push_events = list()

    # этот флаг нужен для безопасной работы с данными между потоками.
    # если False, то работает функция logic.update
    # если True, то функция logic.update не работает, работает рассылка подписки через ws
    update_flag = False

    # обеспечивает запись и чтение logic.xml по очереди
    write_flag = False

    @timeit
    def __init__(self, logic_path):
        self.path_logic = logic_path
        self.read_logic()
        self.crc16 = self.checksum()
        self.obj_logic = self.get_dict()
        for item in self.find_all_items():
            crc = self.checksum(json.dumps(item))
            self.items[item['addr']] = Item(addr=item['addr'], crc=crc, update=False, json_obj=item)

    def read_logic(self):
        if not self.write_flag:
            with open(self.path_logic, 'rb') as f:
                self._header = f.readline()
                self.xml_logic = f.read()
                self.xml_logic = self.xml_logic.replace(b'&', b'#amp')

    def get_xml(self):
        return self.xml_logic.replace(b'#amp', b'&')

    def get_dict(self, xml_logic=''):
        if not self.xml_logic: self.read_logic()
        if not xml_logic: xml_logic = self.xml_logic
        e = ET.XML(xml_logic.decode())
        # self.obj_logic = self._xml2dict(e)
        return self._xml2dict(e)

    def get_item(self, addr):
        keys = self._find_path_2_item(self.obj_logic, 'item', 'addr', addr)
        item = self.obj_logic[keys[0]]

        for key in keys[1:]:
            item = item[key]
        # return json.dumps(item, ensure_ascii=False)
        return item

    def set_item(self, operation, tag, area_name, data):
        if operation == 'append':
            if tag != 'item' or 'addr' not in data:
                return {'type': 'error', 'message': 'Append works only for items with addr'}
            # берем список item и редачим нужный. данные линкуются в общую структуру
            items = self.find_all_items(tag=tag)
            for item in items:
                if item['addr'] == data['addr']:
                    for key, value in data.items():
                        item[key] = value
                    self.write()
                    return {'type': 'response', 'message': 'Append successfully'}
            return {'type': 'error', 'message': 'Not found ' + data['addr']}
        elif operation == 'remove':
            if tag != 'item' or 'addr' not in data:
                return {'type': 'error', 'message': 'Remove works only for items with addr'}
            # берем список item и редачим нужный. данные линкуются в общую структуру
            items = self.find_all_items(tag=tag)
            for item in items:
                if item['addr'] == data['addr']:
                    for key in data.keys():
                        if key != 'addr':
                            item.pop(key)
                    self.write()
                    return {'type': 'response', 'message': 'Removed successfully'}
        elif operation == 'write':
            # если есть адрес - проще всего по нему найти
            if 'addr' in data:
                # берем список item и редачим нужный. данные линкуются в общую структуру
                items = self.find_all_items(tag=tag)
                for cntr in range(len(items)):
                    if items[cntr]['addr'] == data['addr']:
                        # копируем новое и удаляем лишние старые ключи
                        lst = set(items[cntr].keys()) - set(data.keys())
                        for key, value in data.items():
                            items[cntr][key] = value
                        for key in lst:
                            items[cntr].pop(key)
                        self.write()
                        return {'type': 'response', 'message': 'Write successfully'}
            # находим комнату
            area = None
            if area_name == 'smart-house':
                area = self.obj_logic['smart-house']
            else:
                areas = self.find_all_items(tag='area')
                for x in areas:
                    if x['name'] == area_name:
                        area = x
                if area is None:
                    return {'type': 'error', 'message': 'Area not found!'}

            if tag in area:
                # если имеется список итемов с таким тегом, то добавляем
                if isinstance(area[tag], list):
                    area[tag].append(data)
                # если только 1 итем с таким тегом - значит он dict
                # и делаем из него list с добавлением нового итема
                else:
                    area[tag] = [area[tag], data]
            # если с таким тегом вообще нет итемов - делаем dict
            else:
                area[tag] = data
            self.write()
            return {'type': 'response', 'message': 'Write successfully'}
            # if type(apea[tag]) is list:

    def del_item(self, addr):  # not tested
        keys = self._find_path_2_item(self.obj_logic, "item", 'addr', addr)
        if len(keys) == 0:
            return {'type': 'error', 'message': 'Addr not found'}
        else:
            item = self.obj_logic
            for key in keys[:-1]:
                item = item[key]
            # if many items
            if isinstance(item, list):
                item.pop(keys[-1])
            # if 1 item
            elif isinstance(item, dict):
                item.pop(item)
        self.write()
        return {'type': 'response', 'message': 'Delete item successfully'}

    def write(self):
        self.write_flag = True
        with open(self.path_logic, 'wb') as f:
            xml_logic = self._dict2xml(self.obj_logic)
            # костыль что бы вернуть <?xml version="1.0" encoding="UTF-8"?> в исходном виде
            # без него было бы
            # f.write(prettify(dict_to_etree(Dict)).encode('utf-8'))
            xml_logic = self._prettify(xml_logic).replace('#amp', '&')
            xml_logic = xml_logic.replace('&quot;', '"')
            f.write(self._header)
            for line in xml_logic.split("\n")[1:]:
                f.write((line + "\n").encode('utf-8'))
        self.write_flag = False

    @timeit
    def set_xml(self, xml):
        xml = xml.encode('utf-8')
        with open(self.path_logic, 'wb') as f:
            if f.write(xml) == len(xml):
                return True
            else:
                return False

    # -----------------
    #   Function _xml2dict
    #   Parse XML-tree to dict
    #   Example use:
    #       from xml.etree import cElementTree as ET
    #       with open("logic.xml") as f:
    #          e = ET.XML(f.read())
    #       Dict = _xml2dict(e)
    #       pprint(Dict)
    #   Input: xml.etree.cElementTree.Element
    #   Output: dict
    # -----------------
    @timeit
    def _xml2dict(self, tree):
        my_dict = {tree.tag: {} if tree.attrib else None}
        child = list(tree)
        if child:
            dd = defaultdict(list)
            for dc in map(self._xml2dict, child):
                for key, value in dc.items():
                    dd[key].append(value)
            my_dict = {tree.tag: {key: value[0] if len(value) == 1 else value for key, value in dd.items()}}
        if tree.attrib:
            # for attrib and childs with same names
            items = [(key, value) for key, value in tree.attrib.items()]
            for x in range(len(items)):
                if items[x][0] in my_dict[tree.tag]:
                    items[x] = (items[x][0] + '_attrib', items[x][1])

            my_dict[tree.tag].update(items)
        if tree.text:
            # correct \n and \t in scripts-body in logic
            text = tree.text if len(tree.text.strip()) else tree.text.strip()

            if child or tree.attrib:
                if text:
                    my_dict[tree.tag]['plain_text'] = text
            else:
                my_dict[tree.tag] = text
        return my_dict

    # -----------------
    #   Function _find_path_2_item
    #   Find path to item by pair key:value in dict Xml
    #   Input: dict,str,str,str
    #   Output: list or None
    # -----------------
    @timeit
    def _find_path_2_item(self, data, tag, g_key, g_value):
        keys = []
        if type(data) is dict:
            for key in data.keys():
                # если находим тэг
                if tag in data:
                    # если data является листом
                    if type(data[tag]) is list:
                        cntr = 0
                        # то перебираем каждый элемент в поисках ключа с нужным значением
                        for item in data[tag]:
                            if g_key in item:
                                if item[g_key] == g_value:
                                    keys.append(tag)
                                    keys.append(cntr)
                                    return keys
                                # если обнаружили вложенный тег
                                if tag in item:
                                    tmp_keys = self._find_path_2_item(item, tag, g_key, g_value)
                                    if len(tmp_keys) != 0:
                                        keys.append(key)
                                        keys.append(cntr)
                                        for tmp_key in tmp_keys:
                                            keys.append(tmp_key)
                                        return keys
                            cntr += 1
                    # если data не list, то у него либо имеется ключ g_key, либо мы его внутри вообще не найдем
                    elif g_key in data[tag]:
                        if data[tag][g_key] == g_value:
                            keys.append(key)
                            # keys.append(tag)
                            # keys.append(g_key)
                            return keys
                # если тэга на этом уровне не нашли, то пытаемся поискать внутри data[key]
                else:
                    tmp_keys = self._find_path_2_item(data[key], tag, g_key, g_value)
                    if len(tmp_keys) != 0:
                        keys.append(key)
                        for tmp_key in tmp_keys:
                            keys.append(tmp_key)
        # если нам изначально пришел не dict, а list (это должно происходить только в процессе рекурсии)
        elif type(data) is list:
            cntr = 0
            for item in data:
                # то ищем внутри каждого элемента
                tmp_keys = self._find_path_2_item(item, tag, g_key, g_value)
                if len(tmp_keys) != 0:
                    keys.append(cntr)
                    for tmp_key in tmp_keys:
                        keys.append(tmp_key)
                cntr += 1
        return keys

    @timeit
    def _dict2xml(self, my_dict):
        def _to_etree(my_dict, root):
            if not my_dict:
                pass
            elif isinstance(my_dict, str):
                root.text = my_dict
            elif isinstance(my_dict, dict):
                for key, value in my_dict.items():
                    assert isinstance(key, str)
                    # for attrib and childs with same names
                    if key.endswith('_attrib'):
                        key = key.removesuffix('_attrib')

                    if key == 'plain_text':
                        assert isinstance(value, str)
                        root.text = value
                    elif isinstance(value, str):
                        root.set(key, value)
                    elif isinstance(value, list):
                        for e in value:
                            _to_etree(e, ET.SubElement(root, key))
                    else:
                        _to_etree(value, ET.SubElement(root, key))
            else:
                assert my_dict == 'invalid type', (type(my_dict), my_dict)

        assert isinstance(my_dict, dict) and len(my_dict) == 1
        tag, body = next(iter(my_dict.items()))
        node = ET.Element(tag)
        _to_etree(body, node)
        return node

    def _prettify(self, elem):
        from xml.dom import minidom
        rough_string = ET.tostring(elem, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="".join(["\t"]))

    @timeit
    def checksum(self, data=None):
        # if data is None - calculate checksum for logic.xml file
        crc = 0
        if data is None:
            buffer = subprocess.run(f'{tools.home_path}/crc16/crc16 file {self.path_logic}', shell=True,
                                    capture_output=True)
        else:
            buffer = subprocess.run(f'{tools.home_path}/crc16/crc16 string \'{data}\'', shell=True,
                                    capture_output=True)
        crc = buffer.stdout.decode('utf-8')
        crc = int(crc, 16)
        # print(hex(crc))

        return crc

    @timeit
    def update(self):
        if not self.update_flag:
            self.read_logic()

            new_crc = self.checksum()
            if new_crc != self.crc16:
                self.logic_update = True
                self.crc16 = new_crc
                self.update_flag = True

                self.obj_logic = self.get_dict()
                items = self.find_all_items()
                for item in items:
                    item_crc = self.checksum(json.dumps(item))
                    addr: str = item['addr']
                    if addr not in self.items:
                        self.items[addr] = Item(addr=addr, crc=item_crc, update=True, json_obj=item)
                    elif self.items[addr].crc != item_crc:
                        self.items[addr].crc = item_crc
                        self.items[addr].update = True
                        self.items[addr].json_obj = item

    @timeit
    def find_all_items(self, data=None, tag='item'):
        if data is None:
            data = self.obj_logic
        items = []
        if type(data) is dict:
            for key in data.keys():
                # если находим тэг
                if tag in data:
                    # если data[tag] является листом
                    if type(data[tag]) is list:
                        for item in data[tag]:
                            items.append(item)
                            items.extend(self.find_all_items(item, tag))
                    else:
                        items.append(data[tag])
                # если тэга на этом уровне не нашли, то пытаемся поискать внутри data[key]
                else:
                    items.extend(self.find_all_items(data[key], tag))
        # если нам изначально пришел не dict, а list (это должно происходить только в процессе рекурсии)
        elif type(data) is list:
            for part in data:
                # то ищем внутри каждого элемента
                items.extend(self.find_all_items(part, tag))

        return [i for n, i in enumerate(items) if i not in items[:n]]  # убираем дубликаты

    def get_all_states(self):
        copy = dict()
        for addr, item in self.items.items():
            copy[addr] = item.get_state()
        return {'type': 'response', 'data': copy}

    # write Auto mode for heating
    def write_automation(self, addr):
        self.update()

        obj = self.items[addr].json_obj
        if 'automation' in obj:
            # если есть список автоматизаций
            if isinstance(obj['automation'], list):
                cntr = 0
                while cntr < len(obj['automation']):
                    if obj['automation'][cntr]['name'] == 'Auto':
                        # если Авто стоит первый в списке - ничего не нужно делать
                        if not cntr:
                            return False
                        # если Авто стоит не на первом месте - удаляем
                        else:
                            obj['automation'].pop(cntr)
                            cntr -= 1
                    cntr += 1
                # записываем режим Авто первым в списке
                tmp = obj['automation']
                obj['automation'] = [{'name': 'Auto', 'temperature-level': '21'}]
                obj['automation'].extend(tmp)
            # если automation записан как аттрибут
            else:
                if isinstance(obj['automation'], str) and 'automation_attrib' not in obj:
                    # add '_attrib' to exist data
                    obj['automation_attrib'] = obj['automation']
                obj['automation'] = [{'name': 'Auto', 'temperature-level': '21'}]
        # если automation не существует - создаем
        else:
            obj['automation'] = [{'name': 'Auto', 'temperature-level': '21'}]
        self.write()
        time.sleep(1)
        return True
