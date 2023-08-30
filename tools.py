import json
import sys

home_path = sys.argv[0]
index = home_path[::-1].find('/')
home_path = home_path[:-index]


def read_config():
    global home_path
    with open(home_path + '/config') as f:
        config = json.load(f)
    config['home_path'] = home_path
    return config


def read_keys():
    with open(read_config()['sh2_path'] + '/keys.txt') as f:
        return [item.split(' ')[0] for item in f.read().split("\n")]
