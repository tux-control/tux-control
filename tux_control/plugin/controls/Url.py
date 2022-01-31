
from tux_control.plugin.controls.Text import Text


class Url(Text):
    html_type = 'url'

    def __init__(self, placeholder: str = None):
        super().__init__(
            placeholder
        )
