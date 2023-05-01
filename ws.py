from logic import Logic


def test(logic: Logic, args):
    return {
        'type': 'response',
        'message': "test completed"
    }


def get_items(logic: Logic, args):
    return {
        'type': 'response',
        'data': logic.get_json()
    }


def get_item(logic: Logic, args):
    return logic.get_item(*args.values())


def set_item(logic: Logic, args):
    return logic.set_item(*args.values())


def del_item(logic: Logic, args):
    return logic.del_item(*args.values())


def get_state(logic: Logic, args):
    return logic.get_state(*args.values())


commands = {
    "test": test,
    "get_items": get_items,
    "set_item": set_item,
    "del_item": del_item,
    "get_state": get_state
}
