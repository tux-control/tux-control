# -*- coding: utf-8 -*-


import flask
from tux_control.tools.jwt import jwt_required

from tux_control.extensions import socketio, plugin_manager
from tux_control.tools.PaginationList import PaginationList
from tux_control.plugin.exceptions import SetException
from tux_control.plugin.IOnNewPluginConfigItem import IOnNewPluginConfigItem

__author__ = "Adam Schubert"


@socketio.on('plugin-config-item/do-list-all')
@jwt_required()
def do_list_all(data):
    plugin_key = data.get('plugin_key')
    filters = data.get('filters')

    found_plugin = plugin_manager.get_plugin(plugin_key)
    if not found_plugin:
        socketio.emit('plugin-config-item/on-list-all-error', {'message': 'Plugin not found', 'code': 404}, room=flask.request.sid)
        return

    if not found_plugin.is_active:
        socketio.emit('plugin-config-item/on-list-all-error', {'message': 'Plugin is not active', 'code': 400}, room=flask.request.sid)
        return

    filtered_result = list(found_plugin.plugin_config_items)
    found_filters = filters.get('filters')
    if found_filters:
        filter_match_modes = {
            'startsWith': lambda elem, query: elem.startswith(query),
            'contains': lambda elem, query: query in elem,
            'endsWith': lambda elem, query: elem.endswith(query),
            'equals': lambda elem, query: elem == query,
            'notEquals': lambda elem, query: elem != query,
            'in': lambda elem, query: elem in query,
            'lt': lambda elem, query: elem < query,
            'lte': lambda elem, query: elem <= query,
            'gt': lambda elem, query: elem > query,
            'gte': lambda elem, query: elem >= query,
        }

        for found_filter_key, found_filter_options in found_filters.items():
            found_filter_match_mode = filter_match_modes.get(found_filter_options.get('match_mode'))
            filtered_result = list(filter(lambda elem: found_filter_match_mode(getattr(elem, found_filter_key).lower(), found_filter_options.get('value').lower()), filtered_result))

    paginated_list = PaginationList.paginate(filtered_result, filters.get('page'), filters.get('per_page'))

    socketio.emit('plugin-config-item/on-list-all', paginated_list, room=flask.request.sid)


@socketio.on('plugin-config-item/do-get')
@jwt_required()
def do_get(data):
    plugin_key = data.get('plugin_key')
    key = data.get('key')

    found_plugin = plugin_manager.get_plugin(plugin_key)
    if not found_plugin:
        socketio.emit('plugin-config-item/on-get-error', {'message': 'Plugin not found', 'code': 404}, room=flask.request.sid)
        return

    if not found_plugin.is_active:
        socketio.emit('plugin-config-item/on-get-error', {'message': 'Plugin is not active', 'code': 400}, room=flask.request.sid)
        return

    found_plugin_config_item = found_plugin.on_get_plugin_config_item(key)
    if not found_plugin_config_item:
        socketio.emit('plugin-config-item/on-get-error', {'message': 'Plugin config item not found', 'code': 404}, room=flask.request.sid)
        return

    socketio.emit('plugin-config-item/on-get', found_plugin_config_item, room=flask.request.sid)


@socketio.on('plugin-config-item/do-set')
@jwt_required()
def do_set(data):
    plugin_key = data.get('plugin_key')
    plugin_config_item = data.get('plugin_config_item')

    found_plugin = plugin_manager.get_plugin(plugin_key)
    if not found_plugin:
        socketio.emit('plugin-config-item/on-set-error', {'message': 'Plugin not found', 'code': 404}, room=flask.request.sid)
        return

    if not found_plugin.is_active:
        socketio.emit('plugin-config-item/on-set-error', {'message': 'Plugin is not active', 'code': 400}, room=flask.request.sid)
        return

    plugin_config_item_key = plugin_config_item.get('key')

    if not plugin_config_item_key:
        socketio.emit('plugin-config-item/on-set-error', {'message': 'Required key was not provided', 'code': 404}, room=flask.request.sid)
        return

    found_plugin_config_item = found_plugin.on_get_plugin_config_item(plugin_config_item_key)
    if not found_plugin_config_item:
        socketio.emit('plugin-config-item/on-set-error', {'message': 'Plugin config item not found', 'code': 404}, room=flask.request.sid)
        return

    # Modify found config
    try:
        found_plugin.on_set_plugin_config_item(found_plugin.on_set_plugin_config_item_class.from_dict(plugin_config_item))
        socketio.emit('plugin-config-item/on-set', plugin_config_item, room=flask.request.sid)
    except SetException as e:
        socketio.emit('plugin-config-item/on-set-error', {'message': str(e), 'code': 500}, room=flask.request.sid)
    return


@socketio.on('plugin-config-item/do-add')
@jwt_required()
def do_create(data):
    plugin_key = data.get('plugin_key')
    plugin_config_item = data.get('plugin_config_item')

    found_plugin = plugin_manager.get_plugin(plugin_key)
    if not found_plugin:
        socketio.emit('plugin-config-item/on-add-error', {'message': 'Plugin not found', 'code': 404}, room=flask.request.sid)
        return

    if not found_plugin.is_active:
        socketio.emit('plugin-config-item/on-add-error', {'message': 'Plugin is not active', 'code': 400}, room=flask.request.sid)
        return

    if not isinstance(found_plugin, IOnNewPluginConfigItem):
        socketio.emit('plugin-config-item/on-add-error', {'message': 'This plugin cannot create new items', 'code': 400}, room=flask.request.sid)
        return

    # Create config
    try:
        found_plugin.on_new_plugin_config_item(found_plugin.on_new_plugin_config_item_class.from_dict(plugin_config_item))
        socketio.emit('plugin-config-item/on-add', plugin_config_item, room=flask.request.sid)
    except SetException as e:
        socketio.emit('plugin-config-item/on-add-error', {'message': str(e), 'code': 500}, room=flask.request.sid)
    return
