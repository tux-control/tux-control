from typing import List
from tux_control.plugin.PluginConfigOption import PluginConfigOption
from tux_control.plugin.IPluginConfigItem import IPluginConfigItem


class IOnNewPluginConfigItem:
    @property
    def new_item_plugin_config_options(self) -> List[PluginConfigOption]:
        raise NotImplementedError

    def on_new_plugin_config_item(self, plugin_config_item: IPluginConfigItem) -> None:
        raise NotImplementedError

    @property
    def on_new_plugin_config_item_class(self) -> IPluginConfigItem:
        """
        Sets class implementing IPluginConfigItem that we will use for hydration and stuff
        :return:
        """
        raise NotImplementedError
