import decimal
import os
import datetime
import enum
import json
from importlib import import_module
import flask.json
from flask import Flask, url_for, request
from tux_control.blueprints import all_blueprints
from tux_control.socketio_services import all_socketio_services
from yaml import load, SafeLoader
from tux_control.tools.IDictify import IDictify

import tux_control as app_root
from tux_control.extensions import socketio, babel, db, migrate, celery, jwt, cors, plugin_manager

APP_ROOT_FOLDER = os.path.abspath(os.path.dirname(app_root.__file__))
TEMPLATE_FOLDER = os.path.join(APP_ROOT_FOLDER, 'templates')
STATIC_FOLDER = os.path.join(APP_ROOT_FOLDER, 'static')


class MyJSONEncoder(flask.json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # Convert decimal instances to float.
            return float(obj)
        elif isinstance(obj, bytes):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, enum.Enum):
            return obj.value
        elif isinstance(obj, IDictify):
            return obj.to_dict()
        return super(MyJSONEncoder, self).default(obj)


class MyJsonWrapper(object):
    @staticmethod
    def dumps(*args, **kwargs):
        if 'cls' not in kwargs:
            kwargs['cls'] = MyJSONEncoder
        return json.dumps(*args, **kwargs)

    @staticmethod
    def loads(*args, **kwargs):
        return json.loads(*args, **kwargs)


def get_config(config_class_string, yaml_files=None):
    """Load the Flask config from a class.
    Positional arguments:
    config_class_string -- string representation of a configuration class that will be loaded (e.g.
        'pypi_portal.config.Production').
    yaml_files -- List of YAML files to load. This is for testing, leave None in dev/production.
    Returns:
    A class object to be fed into app.config.from_object().
    """
    config_module, config_class = config_class_string.rsplit('.', 1)
    config_obj = getattr(import_module(config_module), config_class)

    # Expand some options.
    celery_fmt = 'tux_control.tasks.{}'
    if getattr(config_obj, 'CELERY_IMPORTS', False):
        config_obj.CELERY_IMPORTS = [celery_fmt.format(m) for m in config_obj.CELERY_IMPORTS]
    for definition in getattr(config_obj, 'CELERYBEAT_SCHEDULE', dict()).values():
        definition.update(task=celery_fmt.format(definition['task']))
    db_fmt = 'tux_control.models.{}'
    if getattr(config_obj, 'DB_MODELS_IMPORTS', False):
        config_obj.DB_MODELS_IMPORTS = [db_fmt.format(m) for m in config_obj.DB_MODELS_IMPORTS]

    # Load additional configuration settings.
    yaml_files = yaml_files or [f for f in [
        os.path.join('/', 'etc', 'tux-control', 'config.yml'),
        os.path.abspath(os.path.join(APP_ROOT_FOLDER, '..', 'config.yml')),
        os.path.join(APP_ROOT_FOLDER, 'config.yml'),
    ] if os.path.exists(f)]
    additional_dict = dict()
    for y in yaml_files:
        with open(y) as f:
            loaded_data = load(f.read(), Loader=SafeLoader)
            if isinstance(loaded_data, dict):
                additional_dict.update(loaded_data)
            else:
                raise Exception('Failed to parse configuration {}'.format(y))

    # Merge the rest into the Flask app config.
    for key, value in additional_dict.items():
        setattr(config_obj, key, value)

    return config_obj


def create_app(config_obj, no_sql=False):

    """Create an application."""
    app = Flask(__name__, template_folder=TEMPLATE_FOLDER, static_folder=STATIC_FOLDER)
    config_dict = dict([(k, getattr(config_obj, k)) for k in dir(config_obj) if not k.startswith('_')])
    app.config.update(config_dict)

    # Import DB models. Flask-SQLAlchemy doesn't do this automatically like Celery does.
    with app.app_context():
        for model in app.config.get('DB_MODELS_IMPORTS', list()):
            import_module(model)

    for bp in all_blueprints:
        import_module(bp.import_name)
        app.register_blueprint(bp)

    for socketio_service in all_socketio_services:
        import_module('tux_control.socketio.{}'.format(socketio_service))

    app.json_encoder = MyJSONEncoder

    def url_for_other_page(page):
        args = request.view_args.copy()
        args['page'] = page
        return url_for(request.endpoint, **args)

    app.jinja_env.globals['url_for_other_page'] = url_for_other_page

    if not no_sql:
        db.init_app(app)

    migrate.init_app(app, db)
    socketio.init_app(
        app,
        message_queue=app.config['SOCKET_IO_MESSAGE_QUEUE'],
        cors_allowed_origins='*',
        json=MyJsonWrapper
    )
    socketio.init_app(app, message_queue=app.config['SOCKET_IO_MESSAGE_QUEUE'])
    babel.init_app(app)
    celery.init_app(app)
    cors.init_app(app)
    jwt.init_app(app)
    plugin_manager.init_app(app, app_root_folder=APP_ROOT_FOLDER)

    with app.app_context():
        import_module('tux_control.middleware')

    return app
