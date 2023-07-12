def preset(self, state):
    return state


def parse_hst(states):
    split_states = [{'state': states[i].to_bytes(1, 'big').hex(' ')} for i in range(4, len(states), 5)]
    # split_states = [{'temperature': states[i]} for i in range(4, len(states), 5)]
    return split_states


def parse_hst2(states):
    split_states = [{'state': bytes(states[index:index + 6]).hex(' ')}
                    for index in range(0, len(states), 6)]

    # split_states = [
    #     {
    #         'on': states[index] & 1,
    #         'mode': states[index] >> 4,
    #         'temperature': states[index + 1],  # нужно добавить t-min
    #         'vane-hor': states[index + 3] & 0x0F,
    #         'vane-ver': states[index + 3] >> 4,
    #         'fan': states[index + 4] & 0x0F
    #     }
    #     for index in range(0, len(states), 6)
    # ]
    return split_states
