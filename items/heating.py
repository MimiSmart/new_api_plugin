def preset(self, state):
    # from server
    if len(state) == 6:
        new_state = [0]
        new_state.extend(state[1:5])
        # manual mode
        if state[5] == 0xFF:
            new_state[0] = state[0] & 1
        # always-off
        elif state[5] == 0xFE:
            new_state[0] = 2
        # auto
        elif state[5] == 0:
            new_state[0] = 3
        state = new_state
    # from client
    elif len(state) == 2:
        if self.state is None:
            state = [state[0], 0, state[1], 0, 0]
        else:
            state = [state[0], self.state[1], state[1], self.state[3], self.state[4]]

    return state


def parse_hst(states):
    split_states = [{'state': bytes(states[index:index + 5]).hex(' ')}
                    for index in range(0, len(states), 5)]
    # split_states = [
    #     # opt0 - видимо вкл/выкл, 0xFA на вкл
    #     # opt1 - дробная сенсора
    #     # opt2 - целая сенсора
    #     # opt3 - дробная установленная
    #     # opt4 - целая установленная
    #     {
    #         'on': 1 if states[index] == 0xFA else 0,
    #         'set_temperature': round(states[index + 4] + (states[index + 3] / 255.0), 2),
    #         'sensor_temperature': round(states[index + 2] + (states[index + 1] / 255.0), 2)
    #     }
    #     for index in range(0, len(states), 5)]
    return split_states


def parse_hst2(states):
    # 0й байт:
    # 0 - выкл в ручном режиме
    # 1 - вкл в ручном режиме
    # 2 - всегда выкл
    # 3 - авто
    # opt1 - дробная установленная
    # opt2 - целая установленная
    # opt3 - дробная сенсора
    # opt4 - целая сенсора

    split_states = [{'state': bytes(states[index:index + 5]).hex(' ')}
                    for index in range(0, len(states), 5)]

    # split_states = [
    #     {
    #         'on': states[index] & 1,
    #         'set_temperature': round(states[index + 2] + (states[index + 1] / 255.0), 2),
    #         'sensor_temperature': round(states[index + 4] + (states[index + 3] / 255.0), 2),
    #         'num_automation': states[index] >> 4 if not states[index + 5] else states[index + 5]
    #     }
    #     for index in range(0, len(states), 6)]
    return split_states
