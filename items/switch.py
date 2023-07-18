def preset(self, state):
    # свитч записывается в историю сразу при изменении
    self.write_history()
    return state
