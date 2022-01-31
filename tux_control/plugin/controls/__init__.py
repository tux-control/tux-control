from tux_control.plugin.controls.IControl import IControl
from tux_control.plugin.controls.Checkbox import Checkbox
from tux_control.plugin.controls.Chips import Chips
from tux_control.plugin.controls.Email import Email
from tux_control.plugin.controls.MultiSelect import MultiSelect
from tux_control.plugin.controls.Number import Number
from tux_control.plugin.controls.Password import Password
from tux_control.plugin.controls.Select import Select
from tux_control.plugin.controls.Slider import Slider
from tux_control.plugin.controls.Text import Text
from tux_control.plugin.controls.Url import Url


controls = [
    Checkbox,
    Chips,
    Email,
    MultiSelect,
    Number,
    Password,
    Select,
    Slider,
    Text,
    Url
]


def get_by_html_type(html_type: str) -> IControl:
    controls_by_html_type = {}
    for control in controls:
        if not issubclass(control, IControl):
            raise ValueError('{} is not instance of IControl'.format(control))
        controls_by_html_type[control.html_type] = control

    found_control = controls_by_html_type.get(html_type)
    if not found_control:
        raise ValueError('Control was not found for html_type={}'.format(html_type))

    return found_control
