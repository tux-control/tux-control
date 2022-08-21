# -*- coding: utf-8 -*-


import flask
from tux_control.tools.jwt import jwt_required
from tux_control.tools.database import filter_to_sqlalchemy, sort_to_sqlalchemy
from tux_control.models.tux_control import Role, Permission
from tux_control.extensions import db, socketio
from tux_control.tools.acl import permission_required

__author__ = "Adam Schubert"


@socketio.on('role/do-list-all')
@jwt_required()
def do_list_all_role(data):
    order_by = sort_to_sqlalchemy(
        data.get('sort_field'),
        int(data.get('sort_order', 1)),
        {
            'name': Role.name,
        },
        Role.created
    )

    roles = Role.query.order_by(order_by)

    per_page = int(data.get('per_page', roles.count()))
    page = int(data.get('page', 1))
    filters = data.get('filters', {})
    roles_filter = filter_to_sqlalchemy(
        filters,
        {
            'name': Role.name,
        }
    )

    paginator = roles.filter(*roles_filter).paginate(page, per_page)

    data_ret = []
    for role in paginator.items:
        data_ret.append(role.to_dict())

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

    socketio.emit('role/on-list-all', return_data, room=flask.request.sid)


@socketio.on('role/do-get')
@jwt_required()
def do_get_role(data):
    role_detail = Role.query.filter_by(id=data.get('id')).first()
    if not role_detail:
        socketio.emit(
            'role/on-get-error',
            {'message': 'Role was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    role_info = role_detail.to_dict()
    socketio.emit('role/on-get', role_info, room=flask.request.sid)


@socketio.on('role/do-update')
@jwt_required()
@permission_required('role.edit')
def do_update_role(data):

    found_role = Role.query.filter_by(id=data.get('id')).first()
    permissions = Permission.query.filter(Permission.id.in_([permission.get('id') for permission in data.get('permissions')])).all()

    if not found_role:
        socketio.emit(
            'role/on-update-error',
            {'message': 'Role was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    found_role.name = data.get('name')
    found_role.permissions = permissions
    db.session.add(found_role)
    db.session.commit()

    socketio.emit('role/on-update', found_role.to_dict(), room=flask.request.sid)


@socketio.on('role/do-create')
@jwt_required()
@permission_required('role.edit')
def do_create_role(data):
    permissions = Permission.query.filter(Permission.id.in_([permission.get('id') for permission in data.get('permissions')])).all()
    role_new = Role()
    role_new.name = data.get('name')
    role_new.permissions = permissions
    db.session.add(role_new)
    db.session.commit()

    socketio.emit('role/on-create', role_new.to_dict(), room=flask.request.sid)


@socketio.on('role/do-delete')
@jwt_required()
def do_delete_role(data):
    role_detail = Role.query.filter_by(id=data.get('id')).first()
    if not role_detail:
        socketio.emit(
            'role/on-delete-error',
            {'message': 'Role was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    role_info = role_detail.to_dict()
    db.session.delete(role_detail)
    db.session.commit()

    socketio.emit('role/on-delete', role_info, room=flask.request.sid)

