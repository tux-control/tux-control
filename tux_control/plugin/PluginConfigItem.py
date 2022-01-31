
from tux_control.plugin.IPluginConfigItem import IPluginConfigItem


class PluginConfigItem(IPluginConfigItem):
    name = 'Test'
    key = 'main'
    is_deletable = True
    is_editable = True

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'key': self.key
        }

