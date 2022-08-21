"""Flask middleware definitions. This is also where template filters are defined.

To be imported by the application.current_app() factory.
"""
import os
from logging import getLogger

from flask import current_app, jsonify, request, has_request_context, g
from celery.signals import worker_process_init
from flask_babel import format_datetime
from tux_control.extensions import babel, db, jwt
from tux_control.models.tux_control import User
from tux_control.tools.helpers import  get_hash
from markupsafe import Markup

try:
    from flask import safe_join
except ImportError:
    from werkzeug.utils import safe_join

LOG = getLogger(__name__)
hash_cache = {}


# Fix Flask-SQLAlchemy and Celery incompatibilities.
@worker_process_init.connect
def celery_worker_init_db(**_):
    """Initialize SQLAlchemy right after the Celery worker process forks.
    This ensures each Celery worker has its own dedicated connection to the MySQL database. Otherwise
    one worker may close the connection while another worker is using it, raising exceptions.
    Without this, the existing session to the MySQL server is cloned to all Celery workers, so they
    all share a single session. A SQLAlchemy session is not thread/concurrency-safe, causing weird
    exceptions to be raised by workers.
    Based on http://stackoverflow.com/a/14146403/1198943
    """
    LOG.debug('Initializing SQLAlchemy for PID {}.'.format(os.getpid()))
    db.init_app(current_app)


# Setup default error templates.
@current_app.errorhandler(400)
@current_app.errorhandler(403)
@current_app.errorhandler(404)
@current_app.errorhandler(500)
def error_handler(e):
    code = getattr(e, 'code', 500)  # If 500, e == the exception.
    return jsonify({'error': code}), code


@current_app.url_defaults
def add_hash_for_static_files(endpoint, values):
    """Add content hash argument for url to make url unique.
    It's have sense for updates to avoid caches.
    """
    if endpoint != 'static':
        return
    filename = values['filename']
    if filename in hash_cache:
        values['hash'] = hash_cache[filename]
        return

    filepath = safe_join(current_app.static_folder, filename)
    if os.path.isfile(filepath):
        with open(filepath, 'rb') as static_file:
            filehash = get_hash(static_file.read(), 8)
            values['hash'] = hash_cache[filename] = filehash


@babel.localeselector
def get_locale():
    # if a user is logged in, use the locale from the user settings
    user = getattr(g, 'user', None)
    if user is not None:
        return user.locale

    if not has_request_context():
        return current_app.config.get('LANGUAGE')

    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(current_app.config['SUPPORTED_LANGUAGES'].keys(), current_app.config.get('LANGUAGE'))


if getattr(jwt, 'user_lookup_loader', None):
    @jwt.user_lookup_loader
    def user_loader_callback(jwt_header: dict, jwt_data: dict) -> User:
        return User.query.get(int(jwt_data['sub']['id']))
elif getattr(jwt, 'user_loader_callback_loader', None):
    @jwt.user_loader_callback_loader
    def user_loader_callback_3(identity) -> User:
        return User.query.get(int(identity['id']))


@babel.timezoneselector
def get_timezone():
    if current_app.config['TIMEZONE']:
        return current_app.config['TIMEZONE']

    user = g.get('user', None)
    if user is not None:
        return user.timezone


@current_app.template_filter('format_datetime')
def format_datetime_filter(date_time):
    return format_datetime(date_time)


# Template filters.
@current_app.template_filter()
def whitelist(value):
    """Whitelist specific HTML tags and strings.
    Positional arguments:
    value -- the string to perform the operation on.
    Returns:
    Markup() instance, indicating the string is safe.
    """
    translations = {
        '&amp;quot;': '&quot;',
        '&amp;#39;': '&#39;',
        '&amp;lsquo;': '&lsquo;',
        '&amp;nbsp;': '&nbsp;',
        '&lt;br&gt;': '<br>',
    }
    escaped = str(Markup.escape(value))  # Escapes everything.
    for k, v in translations.items():
        escaped = escaped.replace(k, v)  # Un-escape specific elements using str.replace.
    return Markup(escaped)  # Return as 'safe'.