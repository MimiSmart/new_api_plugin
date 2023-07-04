def parse_hst(states):
    split_states = [{'state': bytes(states[index:index + 2]).hex(' ')} for index in
                    range(0, len(states), 2)]
    # split_states = [{'state': round(states[index + 1] + (states[index] / 255.0), 2)} for index in
    #                 range(0, len(states), 2)]
    return split_states


def parse_hst2(states):
    split_states = [{'state': bytes(states[index:index + 2]).hex(' ')}
                    for index in range(0, len(states), 2)]
    # split_states = [{'state': round(states[index + 1] + (states[index] / 255.0), 2)} for index in
    #                 range(0, len(states), 2)]
    return split_states
