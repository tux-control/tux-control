# -*- coding: utf-8 -*-


import flask
from tux_control.tools.jwt import jwt_required
from tux_control.tools.database import filter_to_sqlalchemy, sort_to_sqlalchemy
from tux_control.models.tux_control import Permission
from tux_control.extensions import socketio, db
from tux_control.tools.acl import collect_permissions

__author__ = "Adam Schubert"


@socketio.on('permission/do-list-all')
@jwt_required()
def do_list_all_permission(data):
    # Sync permissions

    print(collect_permissions())

    for permission_raw_key, permission_raw_description in collect_permissions().items():
        found_permission = Permission.query.filter_by(identifier=permission_raw_key).one_or_none()
        if not found_permission:
            found_permission = Permission()
            found_permission.identifier = permission_raw_key
        found_permission.name = permission_raw_description
        db.session.add(found_permission)
    db.session.commit()

    order_by = sort_to_sqlalchemy(
        data.get('sort_field'),
        int(data.get('sort_order', 1)),
        {
            'name': Permission.name,
            'identifier': Permission.identifier,
        },
        Permission.created
    )

    permissions = Permission.query.order_by(order_by)

    per_page = int(data.get('per_page', permissions.count()))
    page = int(data.get('page', 1))
    filters = data.get('filters', {})
    permissions_filter = filter_to_sqlalchemy(
        filters,
        {
            'name': Permission.name,
            'identifier': Permission.identifier,
        }
    )

    paginator = permissions.filter(*permissions_filter).paginate(page, per_page)

    data_ret = []
    for permission in paginator.items:
        data_ret.append(permission.to_dict())

    return_data = {
        'has_next': paginator.has_next,
        'has_prev': paginator.has_prev,
        'next_num': paginator.next_num,
        'prev_num': paginator.prev_num,
        'page': paginator.page,
        'pages': paginator.pages,
        'per_page': paginator.per_page,
        'total': paginator.total,
        'data': data_ret,
    }

    socketio.emit('permission/on-list-all', return_data, room=flask.request.sid)


