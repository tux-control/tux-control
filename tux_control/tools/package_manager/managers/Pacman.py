"""
 python-pacman - (c) Jacob Cook 2015
 Licensed under GPLv3
"""

import subprocess
import re
from tux_control.tools.package_manager.managers.IManager import IManager
from tux_control.tools.package_manager.PackageInfo import PackageInfo
from tux_control.tools.package_manager.PackageUpdateInfo import PackageUpdateInfo
from typing import List, Union

ListOfStrings = List[str]


class Pacman(IManager):

    def install(self, packages: ListOfStrings, needed: bool=True, **kwargs) -> None:
        # Install package(s)
        s = self._pacman("-S", packages, ["--needed" if needed else None], **kwargs)
        if s["code"] != 0:
            raise Exception("Failed to install: {0}".format(s["stderr"]))

    def refresh(self, **kwargs) -> None:
        # Refresh the local package information database
        s = self._pacman("-Sy", **kwargs)
        if s["code"] != 0:
            raise Exception("Failed to refresh database: {0}".format(s["stderr"]))

    def upgrade(self, packages: Union[ListOfStrings, None]=None, **kwargs) -> None:
        # Upgrade packages; if unspecified upgrade all packages
        if not packages:
            packages = []

        if packages:
            s = self._pacman("-S", packages, **kwargs)
        else:
            s = self._pacman("-Su", **kwargs)
        if s["code"] != 0:
            raise Exception("Failed to upgrade packages: {0}".format(s["stderr"]))

    def remove(self, packages: ListOfStrings, purge: bool=False, **kwargs) -> None:
        # Remove package(s), purge its files if requested
        s = self._pacman("-Rc{0}".format("n" if purge else ""), packages)
        if s["code"] != 0:
            raise Exception("Failed to remove: {0}".format(s["stderr"]))

    def get_updatable(self, **kwargs) -> List[PackageUpdateInfo]:
        s = self._pacman("-Qu", None, **kwargs)
        if s["code"] != 0:
            return []

        # 'php-fpm 7.2.0-1 -> 7.2.0-2'

        compiled = re.compile(r'^(\S+)\s+(\S+)\s+->\s+(\S+)$')

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
        # List all packages, installed and not installed
        interim, results = {}, []
        s = self._pacman("-Q", **kwargs)
        if s["code"] != 0:
            raise Exception(
                "Failed to get installed list: {0}".format(s["stderr"])
            )
        for x in s["stdout"].split('\n'):
            if not x.split():
                continue
            x = x.split(' ')
            interim[x[0]] = {
                "id": x[0], "version": x[1], "upgradable": False,
                "installed": True
            }
        s = self._pacman("-Sl", **kwargs)
        if s["code"] != 0:
            raise Exception(
                "Failed to get available list: {0}".format(s["stderr"])
            )
        for x in s["stdout"].split('\n'):
            if not x.split():
                continue
            x = x.split(' ')
            if x[1] in interim:
                interim[x[1]]["repo"] = x[0]
                if interim[x[1]]["version"] != x[2]:
                    interim[x[1]]["upgradable"] = x[2]
            else:
                results.append({
                    "id": x[1], "repo": x[0], "version": x[2], "upgradable": False,
                    "installed": False
                })
        for x in interim:
            results.append(interim[x])
        return [PackageInfo(info['id'], info['version']) for info in results]

    def get_installed(self, **kwargs) -> List[PackageInfo]:
        # List all installed packages
        interim = {}
        s = self._pacman("-Q", **kwargs)
        if s["code"] != 0:
            raise Exception(
                "Failed to get installed list: {0}".format(s["stderr"])
            )
        for x in s["stdout"].split('\n'):
            if not x.split():
                continue
            x = x.split(' ')
            interim[x[0]] = {
                "id": x[0], "version": x[1], "upgradable": False,
                "installed": True
            }
        s = self._pacman("-Qu", **kwargs)
        if s["code"] != 0 and s["stderr"]:
            raise Exception(
                "Failed to get upgradable list: {0}".format(s["stderr"])
            )
        for x in s["stdout"].split('\n'):
            if not x.split():
                continue
            x = x.split(' -> ')
            name = x[0].split(' ')[0]
            if name in interim:
                r = interim[name]
                r["upgradable"] = x[1]
                interim[name] = r
        results = []
        for x in interim:
            results.append(interim[x])
        return [PackageInfo(info['id'], info['version']) for info in results]

    def get_available(self, **kwargs) -> List[PackageInfo]:
        # List all available packages
        results = []
        s = self._pacman("-Sl", **kwargs)
        if s["code"] != 0:
            raise Exception(
                "Failed to get available list: {0}".format(s["stderr"])
            )
        for x in s["stdout"].split('\n'):
            if not x.split():
                continue
            x = x.split(' ')
            results.append({"id": x[1], "repo": x[0], "version": x[2]})
        return [PackageInfo(info['id'], info['version']) for info in results]

    def get_info(self, package: str, **kwargs) -> PackageInfo:
        # Get package information from database
        interim = []
        s = self._pacman("-Qi" if self.is_installed(package) else "-Si", package, **kwargs)
        if s["code"] != 0:
            raise Exception("Failed to get info: {0}".format(s["stderr"]))
        for x in s["stdout"].split('\n'):
            if not x.split():
                continue
            if ':' in x:
                x = x.split(':', 1)
                interim.append((x[0].strip(), x[1].strip()))
            else:
                data = interim[-1]
                data = (data[0], data[1] + "  " + x.strip())
                interim[-1] = data
        result = {}
        for x in interim:
            result[x[0]] = x[1]
        return PackageInfo(result['Name'], result['Version'], result['Description'], result['Installed Size'])

    def needs_for(self, packages: ListOfStrings, **kwargs) -> list:
        # Get list of not-yet-installed dependencies of these packages
        s = self._pacman("-Sp", packages, ["--print-format", "%n"], **kwargs)
        if s["code"] != 0:
            raise Exception("Failed to get requirements: {0}".format(s["stderr"]))
        return [x for x in s["stdout"].split('\n') if x]

    def depends_for(self, packages: ListOfStrings, **kwargs) -> list:
        # Get list of installed packages that depend on these
        s = self._pacman("-Rpc", packages, ["--print-format", "%n"], **kwargs)
        if s["code"] != 0:
            raise Exception("Failed to get depends: {0}".format(s["stderr"]))
        return [x for x in s["stdout"].split('\n') if x]

    def is_installed(self, package: str, **kwargs) -> bool:
        # Return True if the specified package is installed
        return self._pacman("-Q", package, **kwargs)["code"] == 0

    def _pacman(self, flags: str, pkgs: Union[ListOfStrings, str, None]=None, eflgs: Union[ListOfStrings, None]=None, env: dict=None):
        # Subprocess wrapper, get all data

        if not pkgs:
            pkgs = []

        if not eflgs:
            eflgs = []

        if not pkgs:
            cmd = ["pacman", "--noconfirm", flags]
        elif type(pkgs) == list:
            cmd = ["pacman", "--noconfirm", flags]
            cmd += pkgs
        else:
            cmd = ["pacman", "--noconfirm", flags, pkgs]
        if eflgs and any(eflgs):
            eflgs = [x for x in eflgs if x]
            cmd += eflgs

        p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, env=env)
        data = p.communicate()
        data = {"code": p.returncode, "stdout": data[0].decode(),
                "stderr": data[1].rstrip(b'\n').decode()}
        return data