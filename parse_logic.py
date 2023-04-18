# -*- coding: utf-8 -*-
import json
from collections import defaultdict
from xml.etree import cElementTree as ET


class Logic:
    _header = ""
    xml_logic = ""
    obj_logic = None

    def get_xml(self):
        with open('logic.xml', 'rb') as f:
            self._header = f.readline()
            self.xml_logic = f.read()
        return self._header + self.xml_logic

    def get_dict(self):
        self.get_xml()  # временно, пока нет отслеживания изменений логики
        e = ET.XML(self.xml_logic.decode())
        self.obj_logic = self._xml2dict(e)
        return self.obj_logic

    def get_item(self, addr):
        self.get_dict()  # временно, пока нет отслеживания изменений логики
        keys = self._find_path_2_item(self.obj_logic, 'item', '@addr', addr)
        item = self.obj_logic[keys[0]]

        for key in keys[1:]:
            item = item[key]
        return json.dumps(item, ensure_ascii=False)

    def get_json(self):
        self.get_dict()  # временно, пока нет отслеживания изменений логики
        return self.obj_logic

    def write(self):
        with open('new_logic.xml', 'wb') as f:
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
            my_dict[tree.tag].update(('@' + key, value) for key, value in tree.attrib.items())
            # my_dict[tree.tag].update((key, value) for key, value in tree.attrib.items())

        if tree.text:
            text = tree.text.strip()
            if child or tree.attrib:
                if text:
                    my_dict[tree.tag]['#text'] = text
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
                            cntr += 1
                    # если data не list, то у него либо имеется ключ g_key, либо мы его внутри вообще не найдем
                    elif g_key in data[tag]:
                        if data[tag][g_key] == g_value:
                            keys.append(key)
                            keys.append(tag)
                            keys.append(g_key)
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
                    if key.startswith('#'):
                        assert key == '#text' and isinstance(value, str)
                        root.text = value
                    elif key.startswith('@'):
                        assert isinstance(value, str)
                        root.set(key[1:], value)
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
