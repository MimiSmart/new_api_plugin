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


def set_item(logic: Logic, args):
    print(args)
    return logic.set_item(*args.values())


def del_item(logic: Logic, args):
    return logic.del_item(*args.values())


commands = {
    "test": test,
    "get_items": get_items,
    "set_item": set_item,
    "del_item": del_item
}
