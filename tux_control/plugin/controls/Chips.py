from tux_control.plugin.controls.IControl import IControl
from tux_control.tools.IDictify import IDictify


class Chips(IControl, IDictify):

    html_type = 'chips'

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
    def from_dict(data: dict) -> 'Chips':
        return Chips(data.get('placeholder'))