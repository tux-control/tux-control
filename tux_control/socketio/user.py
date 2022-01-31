# -*- coding: utf-8 -*-


import flask
from tux_control.tools.jwt import jwt_required
from flask_jwt_extended import get_current_user
from tux_control.tools.database import filter_to_sqlalchemy, sort_to_sqlalchemy
from tux_control.models.tux_control import User, Role
from tux_control.extensions import db, socketio
from tux_control.tools.acl import permission_required

__author__ = "Adam Schubert"


@socketio.on('user/do-list-all')
@jwt_required
def do_list_all_user(data):
    order_by = sort_to_sqlalchemy(
        data.get('sort_field'),
        int(data.get('sort_order', 1)),
        {
            'email': User.email,
            'first_name': User.first_name,
            'last_name': User.last_name,
            'full_name': User.full_name,
            'system_user': User.system_user,
            'created': User.created,
            'updated': User.updated
        },
        User.created
    )

    users = User.query.order_by(order_by)

    per_page = int(data.get('per_page', users.count()))
    page = int(data.get('page', 1))
    filters = data.get('filters', {})
    users_filter = filter_to_sqlalchemy(
        filters,
        {
            'email': User.email,
            'first_name': User.first_name,
            'last_name': User.last_name,
            'full_name': User.full_name,
            'system_user': User.system_user,
            'created': User.created,
            'updated': User.updated
        }
    )

    paginator = users.filter(*users_filter).paginate(page, per_page)

    data_ret = []
    for user in paginator.items:
        data_ret.append(user.to_dict())

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

    socketio.emit('user/on-list-all', return_data, room=flask.request.sid)


@socketio.on('user/do-get')
@jwt_required
def do_get_user(data):
    user_detail = User.query.filter_by(id=data.get('id')).first()
    if not user_detail:
        socketio.emit(
            'user/on-get-error',
            {'message': 'User was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    user_info = user_detail.to_dict()
    socketio.emit('user/on-get', user_info, room=flask.request.sid)


@socketio.on('user/do-update')
@jwt_required
@permission_required('user.edit')
def do_update_user(data):
    current_user = get_current_user()

    found_user = User.query.filter_by(id=data.get('id')).first()
    roles = Role.query.filter(Role.id.in_([role.get('id') for role in data.get('roles')])).all()

    password = data.get('password')

    if not found_user:
        socketio.emit(
            'user/on-update-error',
            {'message': 'User was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    if password:
        found_user.set_password(password)

    found_user.email = data.get('email')
    found_user.first_name = data.get('first_name')
    found_user.last_name = data.get('last_name')
    found_user.system_user = data.get('system_user')
    found_user.roles = roles

    db.session.add(found_user)
    db.session.commit()

    if found_user.id == current_user.id:
        # Current user was updated propagate it to websocket
        socketio.emit('authorization/on-set-current-user', found_user.jsonify(), room=flask.request.sid)

    socketio.emit('user/on-update', found_user.to_dict(), room=flask.request.sid)


@socketio.on('user/do-create')
@jwt_required
@permission_required('user.edit')
def do_create_user(data):
    roles = Role.query.filter(Role.id.in_([role.get('id') for role in data.get('roles')])).all()

    user_new = User()
    user_new.email = data.get('email')
    user_new.first_name = data.get('first_name')
    user_new.last_name = data.get('last_name')
    user_new.system_user = data.get('system_user')
    user_new.set_password(data.get('password'))
    user_new.roles = roles
    db.session.add(user_new)
    db.session.commit()

    socketio.emit('user/on-create', user_new.to_dict(), room=flask.request.sid)


@socketio.on('user/do-delete')
@jwt_required
@permission_required('user.delete')
def do_delete_user(data):
    user_detail = User.query.filter_by(id=data.get('id')).first()
    if not user_detail:
        socketio.emit(
            'user/on-delete-error',
            {'message': 'User was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    user_info = user_detail.to_dict()
    db.session.delete(user_detail)
    db.session.commit()

    socketio.emit('user/on-delete', user_info, room=flask.request.sid)

