from logic import Logic

logic: Logic = None


def test():
    return {
        'type': 'response',
        'message': "test completed"
    }


def get_items():
    return {
        'type': 'response',
        'data': logic.get_json()
    }


commands = {
    "test": test,
    "get_items": get_items
}
