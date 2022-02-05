import pwd
import pam
import os
from pathlib import Path
from typing import Union, Generator, Tuple


class SystemUser:

    def __init__(self, password_database: pwd.struct_passwd):
        self.password_database = password_database
        self.username = password_database.pw_name
        self.id = self.password_database.pw_uid
        self.home_directory = self.password_database.pw_dir
        self.group_id = self.password_database.pw_gid

    def check_password(self, password: str) -> Tuple[str, Union[bool, None]]:
        p = pam.pam()
        if p.authenticate(self.username, password):
            return '', True

        else:
            return p.reason, False

    def chown(self, path: Union[Path, str]) -> None:
        os.chown(path, self.id, self.group_id)


class SystemUserRepository:
    @staticmethod
    def find_by_id(_id: int) -> SystemUser:
        password_database = pwd.getpwuid(_id)
        return SystemUser(password_database)

    @staticmethod
    def find_by_name(name: str) -> Union[SystemUser, None]:
        try:
            password_database = pwd.getpwnam(name)
            return SystemUser(password_database)
        except KeyError:
            return None

    @staticmethod
    def find_all() -> Generator[SystemUser, None, None]:
        for password_database in pwd.getpwall():
            yield SystemUser(password_database)
