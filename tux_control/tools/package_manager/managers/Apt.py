
import subprocess
import re
from tux_control.tools.package_manager.managers.IManager import IManager
from tux_control.tools.package_manager.PackageInfo import PackageInfo
from tux_control.tools.package_manager.PackageUpdateInfo import PackageUpdateInfo
from typing import List, Union

ListOfStrings = List[str]


class Apt(IManager):

    def install(self, packages: ListOfStrings, needed: bool=True, **kwargs) -> None:
        s = self._apt("install", packages)
        if s["code"] != 0:
            raise Exception("Failed to install: {0}".format(s["stderr"]))

    def refresh(self, **kwargs) -> None:
        s = self._apt("update")
        if s["code"] != 0:
            raise Exception("Failed to refresh: {0}".format(s["stderr"]))

    def upgrade(self, packages: ListOfStrings=None, **kwargs) -> None:
        s = self._apt("upgrade", packages)
        if s["code"] != 0:
            raise Exception("Failed to upgrade: {0}".format(s["stderr"]))

    def remove(self, packages: ListOfStrings, purge: bool=False, **kwargs) -> None:
        eflgs = []
        if purge:
            eflgs.append('--purge')

        s = self._apt("remove", packages, eflgs=eflgs)
        if s["code"] != 0:
            raise Exception("Failed to upgrade: {0}".format(s["stderr"]))

    def get_updatable(self, **kwargs) -> List[PackageUpdateInfo]:
        s = self._apt("list", eflgs=['--upgradable'], all_yes=False)
        if s["code"] != 0:
            raise Exception("Failed to get updatable: {0}".format(s["stderr"]))

        compiled = re.compile(r'^(\S+)\/\S+\s+(\S+)\s+\S+\s+\[upgradable from: (\S+)]$')

        data = []
        rows = [x for x in s["stdout"].split('\n') if x]
        for row in rows:
            found = compiled.search(row)
            if found:
                data.append(PackageUpdateInfo(
                    found.group(1),
                    found.group(2),
                    found.group(3),
                ))
        return data

    def get_all(self, **kwargs) -> List[PackageInfo]:
        s = self._apt("list", eflgs=['--all-versions'], all_yes=False)
        if s["code"] != 0:
            raise Exception("Failed to get_all: {0}".format(s["stderr"]))

        compiled = re.compile(r'^(\S+)\/\S+\s+(\S+)\s+\S+$')

        data = []
        rows = [x for x in s["stdout"].split('\n') if x]
        for row in rows:
            found = compiled.search(row)
            if found:
                data.append(PackageInfo(
                    found.group(1),
                    found.group(2)
                ))
        return data

    def get_installed(self, **kwargs) -> List[PackageInfo]:
        s = self._apt("list", eflgs=['--installed'], all_yes=False)
        if s["code"] != 0:
            raise Exception("Failed to get_installed: {0}".format(s["stderr"]))

        compiled = re.compile(r'^(\S+)\/\S+\s+(\S+)\s+\S+\s+\[installed(:?.+|)]$')

        data = []
        rows = [x for x in s["stdout"].split('\n') if x]
        for row in rows:
            found = compiled.search(row)
            if found:
                data.append(PackageInfo(
                    found.group(1),
                    found.group(2)
                ))
        return data

    def get_available(self, **kwargs) -> List[PackageInfo]:
        return self.get_all()

    def get_info(self, package: str, **kwargs) -> PackageInfo:
        s = self._apt("show", package, all_yes=False)
        if s["code"] != 0:
            raise Exception("Failed to get_info: {0}".format(s["stderr"]))

        version_re = re.compile(r'^Version:\s+(\S+)$')
        name_re = re.compile(r'^Package:\s+(\S+)$')
        installed_size_re = re.compile(r'^Installed-Size:\s+(\S+)$')
        description_re = re.compile(r'^Description:(\s+(?:.|\n )+)$')

        rows = [x for x in s["stdout"].split('\n') if x]
        name = None
        version = None
        description = None
        installed_size = None

        for row in rows:
            found_name = name_re.search(row)
            if found_name:
                name = found_name.group(1)

            found_version = version_re.search(row)
            if found_version:
                version = found_version.group(1)

            found_installed_size = installed_size_re.search(row)
            if found_installed_size:
                installed_size = found_installed_size.group(1)

            found_description = description_re.search(row)
            if found_description:
                description = found_description.group(1)

        return PackageInfo(name, version, description, installed_size)

    def is_installed(self, package: str, **kwargs) -> bool:
        # Return True if the specified package is installed
        return self._dpkg('-s', package)['code'] == 0

    def _apt(self, flags: str, pkgs: Union[ListOfStrings, str, None]=None, eflgs: Union[ListOfStrings, None]=None, all_yes: bool = True) -> dict:
        # Subprocess wrapper, get all data

        if not pkgs:
            pkgs = []

        if not eflgs:
            eflgs = []

        cmd = ['apt']

        if all_yes:
            cmd.append('-yq')

        cmd.append(flags)

        if pkgs:
            cmd += pkgs if type(pkgs) == list else [pkgs]

        if eflgs and any(eflgs):
            eflgs = [x for x in eflgs if x]
            cmd += eflgs
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        data = p.communicate()
        data = {"code": p.returncode, "stdout": data[0].decode(),
                "stderr": data[1].rstrip(b'\n').decode()}
        return data

    def _dpkg(self, flags: str, pkgs: Union[ListOfStrings, str, None]=None, eflgs: Union[ListOfStrings, None]=None) -> dict:
        # Subprocess wrapper, get all data

        if not pkgs:
            pkgs = []

        if not eflgs:
            eflgs = []

        if not pkgs:
            cmd = ["dpkg", flags]
        elif type(pkgs) == list:
            cmd = ["dpkg", flags]
            cmd += pkgs
        else:
            cmd = ["dpkg", flags, pkgs]
        if eflgs and any(eflgs):
            eflgs = [x for x in eflgs if x]
            cmd += eflgs
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        data = p.communicate()
        data = {"code": p.returncode, "stdout": data[0].decode(),
                "stderr": data[1].rstrip(b'\n').decode()}
        return data