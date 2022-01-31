from typing import List
from tux_control.tools.package_manager.PackageInfo import PackageInfo
from tux_control.tools.package_manager.PackageUpdateInfo import PackageUpdateInfo


ListOfStrings = List[str]


class IManager:
    def install(self, packages: ListOfStrings, needed: bool=True, **kwargs) -> None:
        raise NotImplementedError

    def refresh(self, **kwargs) -> None:
        raise NotImplementedError

    def upgrade(self, packages: ListOfStrings=None, **kwargs) -> None:
        raise NotImplementedError

    def remove(self, packages: ListOfStrings, purge: bool=False, **kwargs) -> None:
        raise NotImplementedError

    def get_updatable(self, **kwargs) -> List[PackageUpdateInfo]:
        raise NotImplementedError

    def get_all(self, **kwargs) -> List[PackageInfo]:
        raise NotImplementedError

    def get_installed(self, **kwargs) -> List[PackageInfo]:
        raise NotImplementedError

    def get_available(self, **kwargs) -> List[PackageInfo]:
        raise NotImplementedError

    def get_info(self, package_name: str, **kwargs) -> PackageInfo:
        raise NotImplementedError

    def is_installed(self, package: str, **kwargs) -> bool:
        raise NotImplementedError

