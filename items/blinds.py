def preset(self, state):
    # на жалюзи нужно получать данные от сервера, т.к. непонятно когда в каком положении они будут

    # если на жалюзи устанавливается статус с временем хода - игнорим время
    if len(state) == 2:
        state = state[0]
    # если 0xFF - изменить состояние на противоположное
    if state[0] == 0xFF:
        if self.state[0] in [0, 2]:
            state[0] = 3
        elif self.state[0] in [1, 3]:
            state[0] = 2
        # state[0] = self.state[0] ^ 1 if self.state[0] & 1 else self.state[0] | 1
    return state


def parse_hst(states):
    split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
    # split_states = []
    # for item in states:
    #     tmp = {'state': None}
    #     if not item:
    #         tmp['state'] = 'close'
    #     elif item == 0x7D:
    #         tmp['state'] = 'half opened'
    #     elif item == 0xFA:
    #         tmp['state'] = 'opened'
    #     else:
    #         tmp['state'] = 'undefined'
    #     split_states.append(tmp)
    return split_states


def parse_hst2(states):
    split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
    # split_states = [{'state': item} for item in states]
    return split_states
