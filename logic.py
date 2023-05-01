# -*- coding: utf-8 -*-
from collections import defaultdict
from xml.etree import cElementTree as ET

from crc import Calculator, Crc16


class Logic:
    _header = ""
    path_logic = ""
    xml_logic = ""
    obj_logic = None
    crc16 = 0
    updater = None
    state_items = dict()
    event_list = []  # list of addressess of items with update logic event

    def __init__(self, path_logic):
        self.path_logic = path_logic
        data = self.get_xml()
        self.crc16 = self.checksum(data)
        self.obj_logic = self.get_dict()

        # self.updater = Thread(target=self.update())

    def get_xml(self):
        with open(self.path_logic, 'rb') as f:
            self._header = f.readline()
            self.xml_logic = f.read()
        return self._header + self.xml_logic

    def get_dict(self):
        e = ET.XML(self.xml_logic.decode())
        # self.obj_logic = self._xml2dict(e)
        return self._xml2dict(e)

    def get_item(self, addr):
        keys = self._find_path_2_item(self.obj_logic, 'item', 'addr', addr)
        item = self.obj_logic[keys[0]]

        for key in keys[1:]:
            item = item[key]
        # return json.dumps(item, ensure_ascii=False)
        return item

    def get_json(self):
        return self.obj_logic

    def set_item(self, operation, tag, area_name, data):
        if operation == 'append':
            if tag != 'item' or 'addr' not in data:
                return {'type': 'error', 'message': 'Append works only for items with addr'}
            # берем список item и редачим нужный. данные линкуются в общую структуру
            items = self._find_all_items(self.obj_logic, tag)
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
            items = self._find_all_items(self.obj_logic, tag)
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
                items = self._find_all_items(self.obj_logic, tag)
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
                areas = self._find_all_items(self.obj_logic, 'area')
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
        with open(self.path_logic, 'wb') as f:
            # костыль что бы вернуть <?xml version="1.0" encoding="UTF-8"?> в исходном виде
            # без него было бы
            # f.write(prettify(dict_to_etree(Dict)).encode('utf-8'))
            f.write(self._header)
            for line in self._prettify(self._dict2xml(self.obj_logic)).split("\n")[1:]:
                f.write((line + "\n").encode('utf-8'))

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

    def checksum(self, data):
        calculator = Calculator(Crc16.CCITT, optimized=True)
        return calculator.checksum(data)

    # Thread
    def update(self):
        data = self.get_xml()
        new_crc = self.checksum(data)
        if new_crc != self.crc16:
            # if True:
            # тут будет триггериться ивент на обновление логики клиентам
            # не забыть что и на отдельные итемы тоже обнову ннадо делать

            # data = self.get_dict()
            # data2 = self._find_all_items(data)
            # crc_items = dict()
            # for item in data2:
            #     crc_items [item['@addr']] =

            self.obj_logic = self.get_dict()
            self.crc16 = new_crc

    def _find_all_items(self, data, tag='item'):
        items = []
        if type(data) is dict:
            for key in data.keys():
                # если находим тэг
                if tag in data:
                    # если data[tag] является листом
                    if type(data[tag]) is list:
                        for item in data[tag]:
                            items.append(item)
                            tmp_items = self._find_all_items(item, tag)
                            for tmp_item in tmp_items:
                                items.append(tmp_item)
                    else:
                        items.append(data[tag])
                # если тэга на этом уровне не нашли, то пытаемся поискать внутри data[key]
                else:
                    tmp_items = self._find_all_items(data[key], tag)
                    for tmp_item in tmp_items:
                        items.append(tmp_item)
        # если нам изначально пришел не dict, а list (это должно происходить только в процессе рекурсии)
        elif type(data) is list:
            for part in data:
                # то ищем внутри каждого элемента
                tmp_items = self._find_all_items(part, tag)
                for tmp_item in tmp_items:
                    items.append(tmp_item)
        return [i for n, i in enumerate(items) if i not in items[:n]]  # убираем дубликаты
