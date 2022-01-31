from tux_control.tools.package_manager.managers.IManager import IManager
from tux_control.tools.package_manager.managers.Apt import Apt
from tux_control.tools.package_manager.managers.Pacman import Pacman
from tux_control.tools.package_manager.PackageUpdateInfo import PackageUpdateInfo
from tux_control.tools.package_manager.PackageInfo import PackageInfo
from typing import List, Union
import subprocess
import errno

ListOfStrings = List[str]


class PackageManager(IManager):

    def __init__(self):
        try:
            subprocess.Popen(['pacman', '--version'], stderr=subprocess.PIPE, stdout=subprocess.PIPE).wait()
            self.native_package_manager = Pacman()
        except OSError as e:
            if e.errno == errno.ENOENT:
                self.native_package_manager = Apt()
            # handle file not found error.
            else:
                # Something else went wrong while trying to run `pacman`
                raise

    def install(self, packages: ListOfStrings, needed: bool=True, **kwargs) -> None:
        return self.native_package_manager.install(packages, needed, **kwargs)

    def refresh(self, **kwargs) -> None:
        return self.native_package_manager.refresh(**kwargs)

    def upgrade(self, packages: Union[ListOfStrings, None]=None, **kwargs) -> None:
        return self.native_package_manager.upgrade(packages, **kwargs)

    def remove(self, packages: ListOfStrings, purge: bool=False, **kwargs) -> None:
        return self.native_package_manager.remove(packages, purge, **kwargs)

    def get_updatable(self, **kwargs) -> List[PackageUpdateInfo]:
        return self.native_package_manager.get_updatable(**kwargs)

    def get_all(self, **kwargs) -> List[PackageInfo]:
        return self.native_package_manager.get_all(**kwargs)

    def get_installed(self, **kwargs) -> List[PackageInfo]:
        return self.native_package_manager.get_installed(**kwargs)

    def get_available(self, **kwargs) -> List[PackageInfo]:
        return self.native_package_manager.get_available(**kwargs)

    def get_info(self, package: str, **kwargs) -> PackageInfo:
        return self.native_package_manager.get_info(package, **kwargs)

    def is_installed(self, package: str, **kwargs) -> bool:
        return self.native_package_manager.is_installed(package, **kwargs)
