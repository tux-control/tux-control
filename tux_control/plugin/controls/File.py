import enum
from typing import List
from tux_control.plugin.controls.IControl import IControl
from tux_control.tools.IDictify import IDictify


class FilePickerType(enum.Enum):
    ALL = 'all'
    FILE = 'file'
    DIRECTORY = 'directory'


class File(IControl, IDictify):

    html_type = 'file'

    def __init__(self, placeholder: str = None, picker_type: FilePickerType = FilePickerType.ALL,  match_mimetypes: List[str] = None):
        self._placeholder = placeholder
        self.match_mimetypes = match_mimetypes
        self.picker_type = picker_type

    @property
    def placeholder(self) -> str:
        return self._placeholder

    def to_dict(self) -> dict:
        return {
            'placeholder': self.placeholder,
            'html_type': self.html_type,
            'match_mimetypes': self.match_mimetypes,
            'picker_type': self.picker_type.value,
        }

    @staticmethod
    def from_dict(data: dict) -> 'File':
        return File(
            data.get('placeholder'),
        )
