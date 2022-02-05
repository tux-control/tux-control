from flask_jwt_extended import get_current_user
from tux_control.tools.acl import in_permissions
from tux_control.tools.pam import SystemUserRepository, SystemUser


class CurrentUser:

    @staticmethod
    def _get_username() -> str:
        current_user = get_current_user()
        if not current_user:
            raise ValueError('Unable to get current user')
        return current_user.system_user

    @staticmethod
    def get_system_user() -> SystemUser:
        return SystemUserRepository.find_by_name(CurrentUser._get_username())

    @staticmethod
    def has_permission(permission: str):
        return in_permissions(permission)
