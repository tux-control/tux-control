# -*- coding: utf-8 -*-
import os.path
import shutil

import flask
from pathlib import Path
from flask_jwt_extended import current_user
from tux_control.tools.jwt import jwt_required
from tux_control.models.tux_control import Role, Permission
from tux_control.extensions import db, socketio
from tux_control.tools.acl import permission_required
from tux_control.models.FileInfo import FileInfo
from tux_control.plugin.CurrentUser import CurrentUser

__author__ = "Adam Schubert"


@socketio.on('file/do-list-all')
@jwt_required()
def do_list_all_file(data):
    settings = data.get('settings', {})
    reversed_sort_order = True if settings.get('sort_order', 1) == -1 else False
    filters = settings.get('filters', {})
    sort_field = settings.get('sort_field', 'name')
    search_path = Path(data.get('parent_file_info', {}).get('absolute', '/'))

    allowed_sort_fields = ['name', 'created', 'updated']
    if sort_field not in allowed_sort_fields:
        socketio.emit('file/on-list-all-error', {'message': 'This sort field is not allowed'}, room=flask.request.sid)
        return

    glob_string = '*{}*'.format(filters.get('name', {}).get('value')) if filters.get('name') else '*'

    matched_files = search_path.glob(glob_string)

    # Sort dirs first
    files = []
    dirs = []
    for matched_file in matched_files:
        file_info = FileInfo(matched_file)
        if not file_info.is_allowed_file():
            continue

        if matched_file.is_dir():
            dirs.append(file_info)
        elif matched_file.is_file():
            files.append(file_info)

    # Sort
    return_data = sorted(dirs, key=lambda i: getattr(i, sort_field), reverse=reversed_sort_order) + sorted(files, key=lambda i: getattr(i, sort_field), reverse=reversed_sort_order)

    socketio.emit('file/on-list-all', return_data, room=flask.request.sid)


@socketio.on('file/do-get-default')
@jwt_required()
def do_get_default_file(data):
    try:
        default_file_info = FileInfo.from_string(os.path.expanduser('~{}'.format(current_user.system_user)))
    except:
        socketio.emit(
            'file/on-get-default-error',
            {'message': 'Default file was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    socketio.emit('file/on-get-default', default_file_info.to_dict(), room=flask.request.sid)


@socketio.on('file/do-get')
@jwt_required()
def do_get_file(data):

    try:
        file_info = FileInfo.from_string(data.get('path'))
    except:
        socketio.emit(
            'file/on-get-error',
            {'message': 'File was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    socketio.emit('file/on-get', file_info.to_dict(), room=flask.request.sid)


@socketio.on('file/do-update')
@jwt_required()
@permission_required('file.edit')
def do_update_file(data):
    old_file_info_raw = data.get('old_file_info')
    new_file_info_raw = data.get('new_file_info')

    if not new_file_info_raw:
        socketio.emit(
            'file/on-update-error',
            {'message': 'File was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    new_file_parent_absolute = new_file_info_raw.get('parent', {}).get('absolute')
    new_file_parent_info = FileInfo.from_string(new_file_parent_absolute) if new_file_parent_absolute else None

    # Find old file
    old_file_info = FileInfo.from_string(old_file_info_raw.get('absolute')) if old_file_info_raw else None

    if old_file_info and not old_file_info.is_allowed_file():
        socketio.emit(
            'file/on-update-error',
            {'message': 'You have no permission to access this file', 'code': 404},
            room=flask.request.sid
        )
        return

    to_rename = os.path.join(new_file_parent_info.absolute, new_file_info_raw.get('name'))
    if old_file_info:
        # We have old file info... that means renaming
        # Rename the old file to new name from new_file_info_raw
        old_file_info.path.rename(to_rename)
    else:
        # We have no old file info, that means creating, only thing that user can create this way are directories, so lets create a dir
        os.mkdir(to_rename)
        system_user = CurrentUser.get_system_user()
        system_user.chown(to_rename)

    file_info_new = FileInfo.from_string(to_rename)

    socketio.emit('file/on-update', {
        'old_file_info': old_file_info.to_dict() if old_file_info else None,
        'new_file_info': file_info_new.to_dict(),
    }, room=flask.request.sid)


@socketio.on('file/do-delete')
@jwt_required()
def do_delete_file(data):
    file_info_delete = FileInfo.from_string(data.get('absolute'))

    if not (file_info_delete.is_file or file_info_delete.is_dir):
        socketio.emit(
            'file/on-delete-error',
            {'message': 'File was not found', 'code': 404},
            room=flask.request.sid
        )
        return

    if not file_info_delete.is_allowed_file():
        socketio.emit(
            'file/on-delete-error',
            {'message': 'You have no permission to delete this file', 'code': 404},
            room=flask.request.sid
        )
        return

    if file_info_delete.is_file:
        file_info_delete.path.unlink(missing_ok=True)
    elif file_info_delete.is_dir:
        file_info_delete.path.rmdir()

    socketio.emit('file/on-delete', file_info_delete.to_dict(), room=flask.request.sid)

