from typing import List
from tux_control.plugin.IConfigOption import IConfigOption
from tux_control.plugin.controls.IControl import IControl
from tux_control.plugin.validators.IValidator import IValidator
from tux_control.tools.IDictify import IDictify
from tux_control.plugin.controls import get_by_html_type


class PluginConfigOption(IConfigOption, IDictify):

    def __init__(self,
                 key: str,
                 name: str,
                 description: str,
                 control: IControl,
                 validators: List[IValidator] = None,
                 value=None,
                 default_value=None,
                 ):
        self._key = key
        self._value = value
        self._default_value = default_value
        self._name = name
        self._description = description
        self._validators = validators
        self._control = control

    @property
    def key(self) -> str:
        return self._key

    @property
    def default_value(self):
        return self._default_value

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def validators(self) -> List[IValidator]:
        return self._validators

    @property
    def control(self) -> IControl:
        return self._control

    @property
    def value(self):
        return self._value

    def to_dict(self):
        return {
            'key': self._key,
            'default_value': self._default_value,
            'value': self._value,
            'name': self._name,
            'description': self._description,
            'validators': self._validators,
            'control': self._control
        }

    @staticmethod
    def from_dict(data: dict) -> 'PluginConfigOption':
        control = data.get('controls', {})

        return PluginConfigOption(
            key=data.get('key'),
            name=data.get('name'),
            description=data.get('description'),
            control=get_by_html_type(control.get('html_type')).from_dict(control),
            validators=data.get('validators'),
            value=data.get('value'),
            default_value=data.get('default_value')
        )