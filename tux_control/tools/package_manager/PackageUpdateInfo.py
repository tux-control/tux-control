

class PackageUpdateInfo:
    def __init__(self, name: str, from_version: str, to_version: str):
        self.name = name
        self.from_version = from_version
        self.to_version = to_version

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'from_version': self.from_version,
            'to_version': self.to_version
        }