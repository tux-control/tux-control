from typing import List
from tux_control.tools.IDictify import IDictify
from tux_control.plugin.PluginConfigOption import PluginConfigOption


class IPluginConfigItem(IDictify):

    @property
    def key(self) -> str:
        raise NotImplementedError

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def is_deletable(self) -> bool:
        raise NotImplementedError

    @property
    def is_editable(self) -> bool:
        raise NotImplementedError

    @staticmethod
    def from_dict(data: dict) -> 'IPluginConfigItem':
        raise NotImplementedError

    @property
    def plugin_config_options(self) -> List[PluginConfigOption]:
        raise NotImplementedError

    def get_values(self):
        values = {}
        for plugin_config_option in self.plugin_config_options:
            values[plugin_config_option.key] = plugin_config_option.value

        return values
