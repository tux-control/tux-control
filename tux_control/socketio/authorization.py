# -*- coding: utf-8 -*-
import logging

import flask
import datetime
from tux_control.tools.jwt import jwt_required
from flask_jwt_extended import create_access_token, \
    get_current_user, \
    create_refresh_token
from tux_control.models.tux_control import User
from tux_control.extensions import db, socketio
from tux_control.models.AuthorizedUser import AuthorizedUser

__author__ = "Adam Schubert"


@socketio.on('authorization/do-login')
def do_login(data):
    email = data.get('email')
    password = data.get('password')

    user_found = User.query.filter_by(email=email).one_or_none()
    if not user_found:
        socketio.emit('authorization/on-login-error', {'message': 'User not found', 'code': 404}, room=flask.request.sid)
        return

    if not user_found.check_password(password):
        socketio.emit('authorization/on-login-error', {'message': 'Wrong password', 'code': 401}, room=flask.request.sid)
        return

    user_found.last_login = datetime.datetime.now(datetime.timezone.utc)

    db.session.add(user_found)
    db.session.commit()

    return_data = user_found.to_dict()

    access_token = create_access_token(identity=return_data)
    refresh_token = create_refresh_token(identity=return_data)
    if flask.current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES'):
        access_token_expires = datetime.datetime.now(datetime.timezone.utc) + flask.current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES')
        access_token_expires = access_token_expires.isoformat()
    else:
        access_token_expires = None

    if flask.current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES'):
        access_token_expires = datetime.datetime.now(datetime.timezone.utc) + flask.current_app.config.get('JWT_REFRESH_TOKEN_EXPIRES')
        refresh_token_expires = access_token_expires.isoformat()
    else:
        refresh_token_expires = None

    authorized_user = AuthorizedUser(
        access_token=access_token,
        access_token_expires=access_token_expires,
        refresh_token=refresh_token,
        refresh_token_expires=refresh_token_expires,
        user=user_found
    )

    socketio.emit('authorization/on-login', authorized_user, room=flask.request.sid)


@socketio.on('authorization/do-get-current-user')
@jwt_required()
def do_get_current_user(data):
    current_user = get_current_user()
    socketio.emit('authorization/on-get-current-user', current_user.to_dict(), room=flask.request.sid)


@socketio.on('authorization/do-set-current-user')
@jwt_required()
def do_set_current_user(data):
    found_user = User.query.filter_by(id=get_current_user().id).one_or_none()
    found_user.email = data.get('email')
    found_user.first_name = data.get('first_name')
    found_user.last_name = data.get('last_name')
    db.session.add(found_user)
    db.session.commit()
    socketio.emit('authorization/on-set-current-user', found_user.to_dict(), room=flask.request.sid)


@socketio.on('authorization/do-set-current-user-password')
@jwt_required()
def do_set_current_user_password(data):
    old_password = data.get('old_password')
    found_user = User.query.filter_by(id=get_current_user().id).one_or_none()

    if not found_user.check_password(old_password):
        socketio.emit('authorization/on-set-current-user-password-error', {'message': 'Wrong password', 'code': 401}, room=flask.request.sid)
        return

    found_user.set_password(data.get('new_password'))

    db.session.add(found_user)
    db.session.commit()
    socketio.emit('authorization/on-set-current-user-password', found_user.to_dict(), room=flask.request.sid)