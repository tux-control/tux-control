from typing import List
from tux_control.plugin.IConfigOption import IConfigOption
from tux_control.tools.IDictify import IDictify


class PluginConfigHorizontalGroup(IConfigOption, IDictify):
    key = 'plugin_config_horizontal_group'
    default_value = None
    name = 'Plugin config horizontal group'
    description = 'Horizontal grouping element'
    is_required = False
    control = None

    def __init__(self, plugin_config_options: List[IConfigOption]):
        self.plugin_config_options = plugin_config_options

    def to_dict(self):
        return {
            'key': self.key,
            'default_value': self.default_value,
            'name': self.name,
            'description': self.description,
            'is_required': self.is_required,
            'control': self.control,
            'plugin_config_options': self.plugin_config_options
        }
