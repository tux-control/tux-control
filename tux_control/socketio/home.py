# -*- coding: utf-8 -*-


import flask
from tux_control.tools.jwt import jwt_required
from flask_jwt_extended import get_current_user

from tux_control.extensions import socketio

__author__ = "Adam Schubert"


@socketio.on('home/do-get-user-settings')
@jwt_required
def do_list_user_layouts(data):
    current_user = get_current_user()

    socketio.emit('home/on-get-user-settings', current_user.jsonify(), room=flask.request.sid)
