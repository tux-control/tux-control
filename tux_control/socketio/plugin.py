# -*- coding: utf-8 -*-


import flask
from tux_control.tools.jwt import jwt_required

from tux_control.extensions import socketio, plugin_manager

__author__ = "Adam Schubert"


@socketio.on('plugin/do-list-all')
@jwt_required()
def do_list_all(data):
    response_data = []
    for key, plugin in plugin_manager.loaded_plugins.items():
        if not plugin.is_active:
            continue
        response_data.append(plugin.to_dict())

    socketio.emit('plugin/on-list-all', response_data, room=flask.request.sid)


@socketio.on('plugin/do-get')
@jwt_required()
def do_get(data):

    found_plugin = plugin_manager.get_plugin(data.get('key'))
    if not found_plugin:
        socketio.emit('plugin/on-get-error', {'message': 'Plugin not found', 'code': 404}, room=flask.request.sid)
        return

    if not found_plugin.is_active:
        socketio.emit('plugin/on-get-error', {'message': 'Plugin is not active', 'code': 400}, room=flask.request.sid)
        return

    socketio.emit('plugin/on-get', found_plugin, room=flask.request.sid)

