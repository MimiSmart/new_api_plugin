def preset(self, state):
    # 0й - старшие 4 бита автоматизация, младшие вкл-выкл
    # 1й байт - дробная часть установленной температуры
    # 2й байт - целая установленная
    # 3й байт - дробная датчика
    # 4й байт - целая датчика

    # from server
    if len(state) == 6:
        state[0] = state[0] & 1
        # manual mode
        if state[5] == 0xFF:
            # state[0] |= 0<<4
            pass
        # always-off
        elif state[5] == 0xFE:
            state[0] |= 1 << 4
        # auto
        elif state[5] == 0:
            state[0] |= 2 << 4
        # other automations (server2.0)
        else:
            state[0] |= (state[5] + 2) << 4
        state.pop(-1)
    # from client
    elif len(state) <= 2:
        if self.state is None:
            try:
                temp = state[1]
                state = [state[0], 0, state[1], 0, 0]
                # не менять состояние
                if temp == 0xFF:
                    state[2] = 0
            # если пришел 1 байт состояния
            except:
                state = [state[0], 0, 0, 0, 0]

            if not state[0]:
                state[0] = 0
            elif state[0] == 1:
                state[0] = 1
            # always-off
            elif state[0] == 2:
                state[0] = 0x10
            # auto
            elif state[0] == 3:
                state[0] = 0x20
            # other automations (server2.0)
            else:
                state[0] = (state - 1) << 4

        else:
            try:
                state = [state[0], self.state[1], state[1], self.state[3], self.state[4]]
            # если пришел 1 байт состояния
            except:
                state = [state[0], self.state[1], self.state[2], self.state[3], self.state[4]]
            # не менять состояние
            if state[2] == 0xFF:
                state[2] = self.state[2]

            if not state[0]:
                state[0] = 0
            elif state[0] == 1:
                state[0] = 1
            # always-off
            elif state[0] == 2:
                state[0] = 0x10
            # auto
            elif state[0] == 3:
                set_temp = self.state[2] + self.state[1] / 250.0
                sensor_temp = self.state[4] + self.state[3] / 250.0
                state[0] = 0x20 | int(set_temp > sensor_temp)
            # other automations (server2.0)
            else:
                set_temp = self.state[2] + self.state[1] / 250.0
                sensor_temp = self.state[4] + self.state[3] / 250.0
                state[0] = ((state - 1) << 4) | int(set_temp > sensor_temp)
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
