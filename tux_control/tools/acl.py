from functools import wraps
from flask import current_app
from flask_jwt_extended import current_user
from tux_control.extensions import plugin_manager


def in_permissions(checked_permission: str, user=None) -> bool:
    if not user:
        user = current_user

    allowed_permissions = []
    for role in user.roles:
        for permission in role.permissions:
            allowed_permissions.append(permission.identifier)

    return checked_permission in allowed_permissions


def permission_required(permission: str):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if in_permissions(permission):
                # continue
                return f(*args, **kwargs)
            else:
                # Unauthorized
                raise Exception('Unauthorized access')

        return decorated_function

    return decorator


def collect_permissions() -> dict:
    permissions_system = current_app.config.get('PERMISSIONS', {})
    permissions_system.update(plugin_manager.collect_permissions())
    return permissions_system
