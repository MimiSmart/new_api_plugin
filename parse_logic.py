# -*- coding: utf-8 -*-
from collections import defaultdict
from xml.etree import cElementTree as ET


# -----------------
#   Function xml2dict
#   Parse XML-tree to dict
#   Example use:
#       from xml.etree import cElementTree as ET
#       with open("logic.xml") as f:
#          e = ET.XML(f.read())
#       Dict = XmlToDict(e)
#       pprint(Dict)
#   Input: xml.etree.cElementTree.Element
#   Output: dict
# -----------------
def xml2dict(tree):
    my_dict = {tree.tag: {} if tree.attrib else None}
    child = list(tree)
    if child:
        dd = defaultdict(list)
        for dc in map(xml2dict, child):
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
#   Function FindPath2ItemInDictXml
#   Find path to item by pair key:value in dict Xml
#   Input: dict,str,str,str
#   Output: list or None
# -----------------
def FindPath2ItemInDictXml(my_dict, tag, key, value):
    keys = [list(my_dict.keys())[0], 'area']
    if type(my_dict[keys[0]]['area']) != list:
        my_dict[keys[0]]['area'] = [my_dict[keys[0]]['area']]
    if tag == 'item':
        # find in each area
        for x in range(0, len(my_dict[keys[0]]['area'])):
            area = my_dict[keys[0]]['area'][x]
            if 'item' in area:
                if type(area['item']) != list:
                    area['item'] = [area['item']]
                # find in each item
                for y in range(0, len(area['item'])):
                    item = area['item'][y]
                    if key in item.keys():
                        if item[key] == value:
                            keys.append(x)
                            keys.append('item')
                            keys.append(y)
                            return keys
                    elif key == 'id' and item['@addr'].split(':')[0] == value:
                        keys.append(x)
                        keys.append('item')
                        keys.append(y)
                        return keys
    return None


def dict2xml(my_dict):
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


def prettify(elem):
    from xml.dom import minidom
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="".join(["\t"]))


header = ""
with open('logic.xml', 'rb') as f:
    header = f.readline()
    Logic = f.read()
e = ET.XML(Logic.decode())

Dict = xml2dict(e)
with open('new_logic.xml', 'wb') as f:
    # костыль что бы вернуть <?xml version="1.0" encoding="UTF-8"?> в исходном виде
    # без него было бы
    # f.write(prettify(dict_to_etree(Dict)).encode('utf-8'))
    f.write(header)
    for line in prettify(dict2xml(Dict)).split("\n")[1:]:
        f.write((line + "\n").encode('utf-8'))
