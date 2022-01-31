import flask
from typing import List, Iterable
from tux_control.plugin.IPluginConfigItem import IPluginConfigItem
from tux_control.plugin.IOnNewPluginConfigItem import IOnNewPluginConfigItem
from tux_control.plugin.GridColumn import GridColumn
from tux_control.tools.IDictify import IDictify


class IPlugin(IDictify):
    def __init__(self, app: flask.Flask = None, plugin_key: str = None, plugin_config: dict = None) -> None:
        raise NotImplementedError

    @property
    def key(self) -> str:
        """
        plugin key string
        :return:
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        """
        Human-readable string
        :return:
        """
        raise NotImplementedError

    @property
    def icon(self) -> str:
        """
        Icon string
        :return:
        """
        raise NotImplementedError

    @property
    def plugin_config_items(self) -> Iterable[IPluginConfigItem]:
        """
        Returns list of PluginConfig items
        :return:
        """
        raise NotImplementedError

    @property
    def plugin_permissions(self) -> dict:
        raise NotImplementedError

    @property
    def is_active(self) -> bool:
        """
        Is this plugin active?
        Check if this plugins matches its requirements, like installed packages, permissions and so on
        :return:
        """
        raise NotImplementedError

    @property
    def grid_columns(self) -> List[GridColumn]:
        """
        Column names to show in grid list
        :return:
        """
        raise NotImplementedError

    @property
    def on_set_plugin_config_item_class(self) -> IPluginConfigItem:
        """
        Sets class implementing IPluginConfigItem that we will use for hydration and stuff
        :return:
        """
        raise NotImplementedError

    def on_get_plugin_config_item(self, plugin_config_item_key: str) -> IPluginConfigItem:
        """
        Returns data for config item
        :param plugin_config_item_key:
        :return:
        """
        raise NotImplementedError

    def on_set_plugin_config_item(self, plugin_config_item: IPluginConfigItem) -> None:
        """
        Sets data for config item
        :param plugin_config_item:
        :return:
        """
        raise NotImplementedError

    def to_dict(self) -> dict:
        to_return = {
            'key': self.key,
            'name': self.name,
            'icon': self.icon,
            'grid_columns': self.grid_columns,
            'has_on_new': False
        }

        if isinstance(self, IOnNewPluginConfigItem):
            to_return['new_item_plugin_config_options'] = self.new_item_plugin_config_options
            to_return['has_on_new'] = True

        return to_return
