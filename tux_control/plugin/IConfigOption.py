from typing import List
from tux_control.plugin.controls.IControl import IControl
from tux_control.plugin.validators.IValidator import IValidator


class IConfigOption:

    @property
    def key(self) -> str:
        raise NotImplementedError

    @property
    def default_value(self):
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def description(self) -> str:
        raise NotImplementedError

    @property
    def is_required(self) -> bool:
        raise NotImplementedError

    @property
    def control(self) -> IControl:
        raise NotImplementedError

    @property
    def validators(self) -> List[IValidator]:
        raise NotImplementedError

    @staticmethod
    def from_dict(data: dict) -> 'IConfigOption':
        raise NotImplementedError
