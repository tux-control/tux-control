from tux_control.plugin.controls.IControl import IControl
from tux_control.tools.IDictify import IDictify


class Checkbox(IControl, IDictify):

    html_type = 'checkbox'

    def __init__(self, placeholder: str = None):
        self._placeholder = placeholder

    @property
    def placeholder(self):
        return self._placeholder

    def to_dict(self) -> dict:
        return {
            'placeholder': self.placeholder,
            'html_type': self.html_type,
        }

    @staticmethod
    def from_dict(data: dict) -> 'Checkbox':
        return Checkbox(data.get('placeholder'))
