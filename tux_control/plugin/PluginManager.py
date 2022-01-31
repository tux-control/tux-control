import flask
import os
from importlib import import_module
from yaml import load, SafeLoader
from typing import Dict, Union
from pathlib import Path
from tux_control.plugin.IPlugin import IPlugin


class PluginManager:
    name = 'plugin_manager'
    app = None
    app_root_folder = None
    _plugins_config = {}

    loaded_plugins: Dict[str, IPlugin] = {}

    def __init__(self, app: flask.Flask = None, **kwargs):
        if app is not None:
            self.init_app(app, **kwargs)

    def init_app(self, app, app_root_folder: str):
        if not hasattr(app, 'extensions'):
            app.extensions = dict()
        if self.name in app.extensions:
            raise ValueError('Already registered extension {}.'.format(self.name))
        app.extensions[self.name] = self

        self.app = app
        self.app_root_folder = app_root_folder
        self._plugins_config = self._get_plugins_config()

        # Register plugins, not in init, maybe init in app context???
        self._register_plugins()

    def _get_plugins_config(self) -> Dict[str, dict]:
        # Find all plugins confs, merge by name
        plugin_dirs = [f for f in [
            Path(os.path.join('/', 'etc', 'tux-control', 'plugin.d')),
            Path(os.path.abspath(os.path.join(self.app_root_folder, '..', 'plugin.d'))),
            Path(os.path.join(self.app_root_folder, 'plugin.d')),
        ] if os.path.exists(f)]

        yaml_files = {}
        for plugin_dir in plugin_dirs:
            for found_yaml_file in plugin_dir.glob('*.yml'):
                # Override files with same name
                yaml_files[found_yaml_file.stem] = found_yaml_file

        plugins = {}
        for plugin_name, config_path in yaml_files.items():
            with open(config_path, 'r') as f:
                loaded_data = load(f.read(), Loader=SafeLoader)
                if isinstance(loaded_data, dict):
                    plugins[plugin_name] = loaded_data
                else:
                    raise Exception('Failed to parse configuration {}'.format(config_path))

        return plugins

    def _register_plugins(self):
        for plugin_name, plugin_config in self._plugins_config.items():
            extension_cls_name = plugin_config.get('PACKAGE_CLASS')
            cls = extension_cls_name.split('.')[-1]

            if extension_cls_name in self.loaded_plugins:
                raise ValueError('Already registered extension {}.'.format(extension_cls_name))
            self.loaded_plugins[extension_cls_name] = getattr(import_module(extension_cls_name), cls)(extension_cls_name, plugin_config.get('CONFIG'))

    def get_plugin(self, key: str) -> Union[IPlugin, None]:
        return self.loaded_plugins.get(key)

    def collect_permissions(self) -> dict:
        return_dict = {}
        for loaded_plugin_key, loaded_plugin in self.loaded_plugins.items():
            return_dict.update(loaded_plugin.plugin_permissions)

        return return_dict
