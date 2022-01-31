import pwd
import pam
from typing import Union, Generator, Tuple


class User:

    def __init__(self, password_database: pwd.struct_passwd):
        self.password_database = password_database
        self.username = password_database.pw_name
        self.id = self.password_database.pw_uid

    def get_id(self) -> int:
        return self.id

    def check_password(self, password: str) -> Tuple[str, Union[bool, None]]:
        p = pam.pam()
        if p.authenticate(self.username, password):
            return '', True

        else:
            return p.reason, False


class UserRepository(object):
    @staticmethod
    def find_by_id(_id: int) -> User:
        password_database = pwd.getpwuid(_id)
        return User(password_database)

    @staticmethod
    def find_by_name(name: str) -> Union[User, None]:
        try:
            password_database = pwd.getpwnam(name)
            return User(password_database)
        except KeyError:
            return None

    @staticmethod
    def find_all() -> Generator[User, None, None]:
        for password_database in pwd.getpwall():
            yield User(password_database)
