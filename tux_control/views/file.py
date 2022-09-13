import shutil

import flask
import os
import uuid
import re
from pathlib import Path
from flask_babel import gettext
from tux_control.tools.jwt import jwt_required
from tux_control.blueprints import api_file
from tux_control.tools.helpers import mkdir_p
from tux_control.tools.acl import permission_required
from file_thumbnailer.ConverterManager import ConverterManager
from file_thumbnailer.models.Dimensions import Dimensions
from tux_control.application import STATIC_FOLDER
from file_thumbnailer.exceptions import NotSupportedException
from tux_control.models.FileInfo import FileInfo
from tux_control.plugin.CurrentUser import CurrentUser


__author__ = "Adam Schubert"

dimensions_regex = re.compile(r'^((\d+|)x\d+)|(\d+x(\d+|))$')


def partial_response(path: Path, start: int, end: int = None, mimetype: str = None) -> flask.Response:
    buffer_size = 10485760  # 10 MiB
    file_size = os.path.getsize(path.absolute())

    # Determine (end, length)
    if end is None:
        end = start + buffer_size - 1
    end = min(end, file_size - 1)
    end = min(end, start + buffer_size - 1)
    length = end - start + 1

    # Read file
    with path.open('rb') as fd:
        fd.seek(start)
        read_bytes = fd.read(length)
    assert len(read_bytes) == length

    response = flask.Response(
        read_bytes,
        206,
        mimetype=mimetype,
        direct_passthrough=True,
    )
    response.headers.add(
        'Content-Range', 'bytes {0}-{1}/{2}'.format(
            start, end, file_size,
        ),
    )
    response.headers.add(
        'Accept-Ranges', 'bytes'
    )
    return response


def get_range(bytes_range: str):
    m = re.match(r'bytes=(?P<start>\d+)-(?P<end>\d+)?', bytes_range)
    if m:
        start = m.group('start')
        end = m.group('end')
        start = int(start)
        if end is not None:
            end = int(end)
        return start, end
    else:
        return 0, None


@api_file.route('/upload', methods=['POST'])
@jwt_required()
@permission_required('file.edit')
def begin_file_upload():
    parent_file = flask.request.json.get('parent_file', {})

    uploads_tmp_dir = os.path.join(flask.current_app.config.get('DATA_STORAGE'), 'uploads')
    mkdir_p(uploads_tmp_dir)

    upload_id = str(uuid.uuid4())
    upload_tmp_file = os.path.join(uploads_tmp_dir, '{}.part'.format(upload_id))
    with open(upload_tmp_file, mode='a'):
        pass

    upload_tmp_file_info = os.path.join(uploads_tmp_dir, '{}.info'.format(upload_id))
    with open(upload_tmp_file_info, mode='w') as info_file:
        flask.json.dump(parent_file, info_file)

    return flask.jsonify({
        'id': upload_id,
        'finished': False,
        'file': None,
    }), 200


@api_file.route('/upload', methods=['PUT'])
@jwt_required()
@permission_required('file.edit')
def upload_file():
    file_info = None
    finished = False
    chunk_file = flask.request.files.get('chunk')
    offset = int(flask.request.form.get('offset'))
    size = int(flask.request.form.get('size'))
    index = int(flask.request.form.get('index'))
    chunks = int(flask.request.form.get('chunks'))
    upload_id = flask.request.form.get('id')

    uploads_tmp_dir = os.path.join(flask.current_app.config.get('DATA_STORAGE'), 'uploads')
    mkdir_p(uploads_tmp_dir)

    upload_tmp_file = os.path.join(uploads_tmp_dir, '{}.part'.format(upload_id))
    upload_tmp_file_info = os.path.join(uploads_tmp_dir, '{}.info'.format(upload_id))
    if not os.path.isfile(upload_tmp_file):
        return flask.jsonify({'message': gettext('Unknown upload.')}), 400

    with open(upload_tmp_file, 'ab') as chunk_handle:
        chunk_handle.seek(offset)
        chunk_handle.write(chunk_file.stream.read())

    if index + 1 == chunks:
        _, file_ext_with_dot = os.path.splitext(chunk_file.filename)
        file_ext = file_ext_with_dot.strip('.')
        tmp_upload_file = os.path.join(uploads_tmp_dir, '{}.{}'.format(upload_id, file_ext))

        try:
            if size != os.path.getsize(upload_tmp_file):
                raise Exception(gettext('Size does not match!'))

            os.rename(upload_tmp_file, tmp_upload_file)

            # Grab our file and move it where we need
            with open(upload_tmp_file_info, 'r') as parent_info_file:
                parent_file_info = flask.json.load(parent_info_file)

            to_rename = os.path.join(parent_file_info.get('absolute'), chunk_file.filename)
            shutil.move(tmp_upload_file, to_rename)

            CurrentUser.get_system_user().chown(to_rename)

            file_info = FileInfo.from_string(to_rename)

        except Exception as e:
            return flask.jsonify({'message': str(e)}), 400
        finally:
            if os.path.isfile(tmp_upload_file):
                os.remove(tmp_upload_file)

            if os.path.isfile(upload_tmp_file_info):
                os.remove(upload_tmp_file_info)

        finished = True

    return flask.jsonify({
        'id': upload_id,
        'finished': finished,
        'file': file_info,
    }), 200


@api_file.route('/download', methods=['GET'])
@jwt_required()
@permission_required('file.read')
def download_file():
    path_raw = flask.request.args.get('path')
    if not path_raw:
        return flask.jsonify({'message': gettext('Missing required parameter "path".')}), 400

    path_info = FileInfo.from_string(path_raw, False)
    if not path_info.is_file:
        return flask.jsonify({'message': gettext('Requested file was not found.')}), 404

    if not path_info.is_allowed_file():
        return flask.jsonify({'message': gettext('You have no permission to read this file.')}), 400

    return flask.send_file(
        path_info.absolute,
        path_info.mime_type,
        as_attachment=True,
        attachment_filename=path_info.name
    ), 200


@api_file.route('/get', methods=['GET'])
@jwt_required()
@permission_required('file.read')
def get_file():
    path_raw = flask.request.args.get('path')
    if not path_raw:
        return flask.jsonify({'message': gettext('Missing required parameter "path".')}), 400

    path_info = FileInfo.from_string(path_raw, False)
    if not path_info.is_file:
        return flask.jsonify({'message': gettext('Requested file was not found.')}), 404

    if not path_info.is_allowed_file():
        return flask.jsonify({'message': gettext('You have no permission to read this file.')}), 400

    bytes_range = flask.request.headers.get('Range')
    if bytes_range:
        start, end = get_range(bytes_range)
        return partial_response(path_info.path, start, end, path_info.mime_type)

    return flask.send_file(
        path_info.absolute,
        path_info.mime_type,
        download_name=path_info.name
    ), 200


@api_file.route('/thumbnail', methods=['GET'])
@jwt_required()
@permission_required('file.read')
def get_thumbnail():
    path_raw = flask.request.args.get('path')
    if not path_raw:
        return flask.jsonify({'message': gettext('Missing required parameter "path".')}), 400

    path_info = FileInfo.from_string(path_raw, False)
    if not path_info.is_file:
        return flask.jsonify({'message': gettext('Requested file was not found.')}), 404

    dimensions = flask.request.args.get('dimensions')
    thumbnail_tmp_dir = os.path.join(flask.current_app.config.get('DATA_STORAGE'), 'thumbnails')
    mkdir_p(thumbnail_tmp_dir)

    if not path_info.is_allowed_file():
        return flask.jsonify({'message': gettext('You have no permission to thumbnail this file.')}), 400

    filename_parts_builder = [path_info.name]

    if dimensions:
        if dimensions_regex.match(dimensions):
            filename_parts_builder.append(dimensions)
        else:
            return flask.jsonify({'message': gettext('Dimensions have a wrong format.')}), 400

    thumbnail_storage_chunk = os.path.join(thumbnail_tmp_dir, path_info.name[:2])
    mkdir_p(thumbnail_storage_chunk)
    thumbnail_filename = '{}.{}'.format('_'.join(filename_parts_builder), 'jpg')
    thumbnail_path = os.path.join(thumbnail_storage_chunk, thumbnail_filename)

    if not os.path.isfile(thumbnail_path):
        # Generate TMP file and return it
        if dimensions:
            requested_width, requested_height = [int(part) if part else None for part in dimensions.split('x')]
        else:
            requested_width, requested_height = None, 100

        try:
            converter_manager = ConverterManager()
            converter = converter_manager.from_file(path_info.absolute)
            thumbnail = converter.to_image_bytes(Dimensions(requested_width, requested_height))
            with open(thumbnail_path, 'wb') as f:
                f.write(thumbnail)
        except (NotSupportedException, FileNotFoundError):
            ico_folder = os.path.join(STATIC_FOLDER, 'ico')
            ico_filename = '{}.jpg'.format(path_info.suffix)
            ico_path = os.path.join(ico_folder, ico_filename)

            if not os.path.isfile(ico_path):
                ico_filename = 'txt.jpg'

            return flask.send_from_directory(ico_folder, ico_filename)

    return flask.send_from_directory(thumbnail_storage_chunk, thumbnail_filename)
