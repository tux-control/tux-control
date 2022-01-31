

class PackageInfo:
    def __init__(self, name: str, version: str, description: str = None, installed_size: str = None):
        self.name = name
        self.version = version
        self.description = description
        self.installed_size = installed_size

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description
        }