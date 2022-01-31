"""Flask and other extensions instantiated here.

To avoid circular imports with views and create_app(), extensions are instantiated here. They will be initialized
(calling init_app()) in application.py.
"""
import os
from logging import getLogger
import tux_control as app_root
from flask_socketio import SocketIO
from raven.contrib.flask import Sentry
from flask_babel import Babel
from flask_celery import Celery
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from tux_control.plugin.PluginManager import PluginManager
from tux_control.tools.package_manager.PackageManager import PackageManager

LOG = getLogger(__name__)
APP_ROOT_FOLDER = os.path.abspath(os.path.dirname(app_root.__file__))
MIGRATE_ROOT_FOLDER = os.path.abspath(os.path.join(APP_ROOT_FOLDER, 'migrations'))


socketio = SocketIO()
sentry = Sentry()
babel = Babel()
celery = Celery()
db = SQLAlchemy()
migrate = Migrate(directory=MIGRATE_ROOT_FOLDER)
package_manager = PackageManager()
plugin_manager = PluginManager()
jwt = JWTManager()
cors = CORS()
