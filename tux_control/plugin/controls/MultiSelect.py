from tux_control.plugin.controls.IControl import IControl
from tux_control.tools.IDictify import IDictify


class MultiSelect(IControl, IDictify):

    html_type = 'multiselect'

    def __init__(self, options: list, placeholder: str = None):
        self._placeholder = placeholder
        self.options = options

    @property
    def placeholder(self) -> str:
        return self._placeholder

    def to_dict(self) -> dict:
        return {
            'placeholder': self.placeholder,
            'html_type': self.html_type,
            'options': self.options
        }

    @staticmethod
    def from_dict(data: dict) -> 'MultiSelect':
        return MultiSelect(data.get('options'), data.get('placeholder'))