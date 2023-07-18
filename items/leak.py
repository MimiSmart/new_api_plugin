def preset(self, state):
    return state


def parse_hst(states):
    split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
    # split_states = [{'state': item} for item in states]
    return split_states


def parse_hst2(states):
    split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
    # split_states = [{'state': item} for item in states]
    return split_states
