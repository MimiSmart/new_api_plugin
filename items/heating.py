def preset(state):
    # тут будет 2 варианта. 2 байта если по апи кто то устанавливает. 6 байт если пришло от старого сервера
    # pass

    # если 0xFF - изменить состояние на противоположное
    if state[0] == 0xFF:
        state[0] = self.state[0] ^ 1 if self.state[0] & 1 else self.state[0] | 1
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
    # 0 - выкл, переводит в ручной режим
    # 1 - вкл, переводит в ручной режим
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
