from tux_control.plugin.controls.Number import Number


class Slider(Number):
    html_type = 'slider'

    def __init__(self, placeholder: str = None, min_value: int = None, max_value: int = None, step: float = None):
        super(Slider, self).__init__(placeholder, min_value, max_value, step)
