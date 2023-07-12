def preset(self, state):
    # если диммеру устанавливается статус с временем изменения яркости - игнорим время
    if len(state) == 3:
        state = state[:2]
    # если 0xFF - изменить состояние на противоположное
    if state[0] == 0xFF:
        state = self.state[0] ^ 1 if self.state[0] & 1 else self.state[0] | 1
    # если 0xFE - не изменять состояние
    for index in range(len(state)):
        if state[index] == 0xFE:
            state[index] = self.state[index]
    return state


def parse_hst(states):
    split_states = [{'state': bytes(states[index:index + 2]).hex(' ')}
                    for index in range(0, len(states), 2)]
    # split_states = [
    #     {
    #         'on': states[index] & 1,
    #         'brightness': round(int((states[index + 1]) * 100 / 255.0), 1)
    #     }
    #     for index in range(0, len(states), 2)
    # ]
    return split_states


def parse_hst2(states):
    split_states = [{'state': bytes(states[index:index + 2]).hex(' ')}
                    for index in range(0, len(states), 2)]
    # split_states = [
    #     {
    #         'on': states[index] & 1,
    #         'brightness': round(int((states[index + 1]) * 100 / 255.0), 1)
    #     }
    #     for index in range(0, len(states), 2)
    # ]
    return split_states
