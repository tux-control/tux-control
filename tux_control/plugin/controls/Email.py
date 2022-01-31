
from tux_control.plugin.controls.Text import Text


class Email(Text):
    html_type = 'email'

    def __init__(self, placeholder: str = None):
        super().__init__(
            placeholder
        )
