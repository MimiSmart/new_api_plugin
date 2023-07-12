def preset(self, state):
    # если rgb устанавливается статус с временем изменения яркости - игнорим время
    if len(state) == 5:
        state = state[:4]
    # если 0xFF - изменить состояние на противоположное
    if state[0] == 0xFF:
        state[0] = self.state[0] ^ 1 if self.state[0] & 1 else self.state[0] | 1

    # если 0xFE - не изменять состояние
    for index in range(len(state)):
        if state[index] == 0xFE:
            state[index] = self.state[index]
    return state


def parse_hst(states):
    # rgb in old history save only value (brightness)
    split_states = [{'state': item.to_bytes(1, 'big').hex(' ')} for item in states]
    # split_states = [
    #     {'on': item > 0,
    #      'value': item if item > 0 else 0
    #      }
    #     for item in states]
    return split_states


def parse_hst2(states):
    split_states = [{'state': bytes(states[index:index + 4]).hex(' ')}
                    for index in range(0, len(states), 4)]
    # split_states = [
    #     {
    #         'on': states[index] & 1,
    #         'value': round(int((states[index + 1]) * 100 / 255.0), 1),
    #         'saturation': round(int((states[index + 2]) * 100 / 255.0), 1),
    #         'hue': round(int((states[index + 3]) * 100 / 255.0), 1),
    #     }
    #     for index in range(0, len(states), 4)
    # ]
    return split_states
