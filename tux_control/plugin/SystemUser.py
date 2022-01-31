import os
from flask_jwt_extended import get_current_user
from tux_control.tools.acl import in_permissions


class SystemUser:

    @staticmethod
    def get_username() -> str:
        current_user = get_current_user()
        if not current_user:
            raise ValueError('Unable to get current user')
        return current_user.system_user

    @staticmethod
    def get_home_dir() -> str:
        return os.path.expanduser('~{}'.format(SystemUser.get_username()))

    @staticmethod
    def has_permission(permission: str):
        return in_permissions(permission)
