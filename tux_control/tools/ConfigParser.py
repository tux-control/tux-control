
import yaml
from typing import Optional, Type
from types import TracebackType
from pathlib import Path


class ConfigParser:
    configuration = {}

    def __init__(self, file_path: Path):
        self.file_path = file_path
        if file_path.is_file():
            with file_path.open('r') as f:
                loaded_data = yaml.load(f, Loader=yaml.SafeLoader)
                if isinstance(loaded_data, dict):
                    self.configuration.update(loaded_data)

    def save(self):
        with self.file_path.open('w') as f:
            yaml.dump(self.configuration, f, default_flow_style=False, allow_unicode=True)

    def get(self, key: str, default: any = None):
        return self.configuration.get(key, default)

    def set(self, key: str, value: any):
        self.configuration[key] = value

    def __setitem__(self, key, value):
        self.set(key, value)

    def __getitem__(self, key):
        return self.get(key)

    def close(self) -> None:
        self.save()

    def __enter__(self) -> 'ConfigParser':
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> None:
        self.close()
