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


def get_state(logic: Logic, args):
    return logic.state_items[args['addr']]
    # if args['addr'] is list:
    #     response = dict()
    #     for addr in args['addr']:
    #         try:
    #             response[addr] = logic.state_items[addr]
    #         except:
    #             response[addr] = None
    #     return response
    # elif args['addr'] is str:
    #     try:
    #         response = logic.state_items[args['addr']]
    #     except:
    #         response = None
    #     return response


commands = {
    "test": test,
    "get_items": get_items,
    "set_item": set_item,
    "del_item": del_item,
    "get_state": get_state
}
