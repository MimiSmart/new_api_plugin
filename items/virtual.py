def preset(self, state):
    # если 0xFF - изменить состояние на противоположное
    if state[0] == 0xFF:
        state[0] = self.state[0] ^ 1 if self.state[0] & 1 else self.state[0] | 1
    return state


def parse_hst(states):
    return [{'state': (item & 1).to_bytes(1, 'big').hex(' ')} for item in states]


def parse_hst2(states):
    split_states = [{'state': (item & 1).to_bytes(1, 'big').hex(' ')} for item in states]
    # split_states = [{'state': item & 1} for item in states]
    return split_states
