from tux_control.plugin.controls.IControl import IControl
from tux_control.tools.IDictify import IDictify


class Select(IControl, IDictify):

    html_type = 'select'

    def __init__(self, options: list, placeholder: str=None):
        self._placeholder = placeholder
        self.options = [{
            'label': '--Select option --',
            'value': None,
        }] + options

    @property
    def placeholder(self):
        return self._placeholder

    def to_dict(self) -> dict:
        return {
            'placeholder': self.placeholder,
            'html_type': self.html_type,
            'options': self.options
        }

    @staticmethod
    def from_dict(data: dict) -> 'Select':
        return Select(
            data.get('options'),
            data.get('placeholder'),
        )
