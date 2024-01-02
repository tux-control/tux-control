#!/usr/bin/env python3
"""Main entry-point into the 'TuxControl' Flask and Socket.io application.

This is a Tux control

License: PROPRIETARY
Website: https://gitlab.salamek.cz/sadam/tux-control.git

Command details:
    server                      Run the application using the Flask Development
                                Server. Auto-reloads files when they change.
    celerydev                   Starts a Celery worker with Celery Beat in the same
                                process.
    create_all                  Only create database tables if they don't exist and
                                then exit.
    celerybeat                  Run a Celery Beat periodic task scheduler.
    celeryworker                Run a Celery worker process.
    list_routes                 List all available routes.
    post_install                Post install script.
    refresh_package_info        Post install script.
    db                          Migrations.
    user                        User control.
    set_user                    Set/Create user from CLI.

Usage:
    tux-control server [-p NUM] [-l DIR] [--config_prod]
    tux-control list_routes
    tux-control celerydev [-l DIR] [--config_prod]
    tux-control celerybeat [-s FILE] [--pid=FILE] [-l DIR] [--config_prod]
    tux-control celeryworker [-n NUM] [-l DIR] [--config_prod]
    tux-control post_install [--config_prod]
    tux-control create_all [--config_prod]
    tux-control user <action> <email> [--config_prod]
    tux-control set_user <email> <password> <system_user> [--config_prod]
    tux-control refresh_package_info [--config_prod]
    tux-control db [<db_action>...] [--config_prod]
    tux-control (-h | --help)

Options:
    --config_prod               Load the production configuration instead of
                                development.
    -l DIR --log_dir=DIR        Log all statements to file in this directory
                                instead of stdout.
                                Only ERROR statements will go to stdout. stderr
                                is not used.
    -n NUM --name=NUM           Celery Worker name integer.
                                [default: 1]
    --pid=FILE                  Celery Beat PID file.
                                [default: ./celery_beat.pid]
    -p NUM --port=NUM           Flask will listen on this port number.
    -s FILE --schedule=FILE     Celery Beat schedule database file.
                                [default: ./celery_beat.db]
"""

import eventlet
import hashlib
import logging
import logging.handlers
import os
import random
import signal
import subprocess
import sys
import urllib.parse
from functools import wraps

import flask
from docopt import docopt
from flask_migrate import stamp
from celery.app.log import Logging
from celery.utils.nodenames import default_nodename, host_format, node_format
from pathlib import Path
from tux_control.extensions import socketio, db, celery
from tux_control.tasks.tux_control import package_manger_update
from tux_control.tools.ConfigParser import ConfigParser
from tux_control.application import create_app, get_config
from tux_control.models.tux_control import Package, User, Role, Permission
from tux_control.tools.packages import get_control_packages, refresh_package
from tux_control.tools.acl import collect_permissions

OPTIONS = docopt(__doc__)


class CustomFormatter(logging.Formatter):
    LEVEL_MAP = {logging.FATAL: 'F', logging.ERROR: 'E', logging.WARN: 'W', logging.INFO: 'I', logging.DEBUG: 'D'}

    def format(self, record):
        record.levelletter = self.LEVEL_MAP[record.levelno]
        return super(CustomFormatter, self).format(record)


def setup_logging(name=None, level=logging.DEBUG) -> None:
    """Setup Google-Style logging for the entire application.

    At first I hated this but I had to use it for work, and now I prefer it. Who knew?
    From: https://github.com/twitter/commons/blob/master/src/python/twitter/common/log/formatters/glog.py

    Always logs DEBUG statements somewhere.

    Positional arguments:
    name -- Append this string to the log file filename.
    """
    log_to_disk = False
    if OPTIONS['--log_dir']:
        if not os.path.isdir(OPTIONS['--log_dir']):
            print('ERROR: Directory {} does not exist.'.format(OPTIONS['--log_dir']))
            sys.exit(1)
        if not os.access(OPTIONS['--log_dir'], os.W_OK):
            print('ERROR: No permissions to write to directory {}.'.format(OPTIONS['--log_dir']))
            sys.exit(1)
        log_to_disk = True

    fmt = '%(levelletter)s%(asctime)s.%(msecs).03d %(process)d %(filename)s:%(lineno)d] %(message)s'
    datefmt = '%m%d %H:%M:%S'
    formatter = CustomFormatter(fmt, datefmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console_handler)

    if log_to_disk:
        file_name = os.path.join(OPTIONS['--log_dir'], 'tux-control_{}.log'.format(name))
        file_handler = logging.handlers.TimedRotatingFileHandler(file_name, when='d', backupCount=7)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


def log_messages(app) -> None:
    """Log messages common to Tornado and devserver."""
    log = logging.getLogger(__name__)
    log.info('Server is running at http://{}:{}/'.format(app.config['HOST'], app.config['PORT']))
    log.info('Flask version: {}'.format(flask.__version__))
    log.info('DEBUG: {}'.format(app.config['DEBUG']))
    log.info('STATIC_FOLDER: {}'.format(app.static_folder))


def parse_options():
    """Parses command line options for Flask.

    Returns:
    Config instance to pass into create_app().
    """
    # Figure out which class will be imported.
    if OPTIONS['--config_prod']:
        config_class_string = 'tux_control.config.Production'
    else:
        config_class_string = 'tux_control.config.Config'
    config_obj = get_config(config_class_string)

    # Force port from commandline
    if OPTIONS['--port']:
        if not OPTIONS['--port'].isdigit():
            print('ERROR: Port should be a number.')
            sys.exit(1)
        config_obj.PORT = OPTIONS['--port']

    return config_obj


def command(name: str = None):
    """Decorator that registers the chosen command/function.

    If a function is decorated with @command but that function name is not a valid "command" according to the docstring,
    a KeyError will be raised, since that's a bug in this script.

    If a user doesn't specify a valid command in their command line arguments, the above docopt(__doc__) line will print
    a short summary and call sys.exit() and stop up there.

    If a user specifies a valid command, but for some reason the developer did not register it, an AttributeError will
    raise, since it is a bug in this script.

    Finally, if a user specifies a valid command and it is registered with @command below, then that command is "chosen"
    by this decorator function, and set as the attribute `chosen`. It is then executed below in
    `if __name__ == '__main__':`.

    Doing this instead of using Flask-Script.

    Positional arguments:
    func -- the function to decorate
    """

    def function_wrap(func):

        @wraps(func)
        def wrapped():
            return func()

        command_name = name if name else func.__name__

        # Register chosen function.
        if command_name not in OPTIONS:
            raise KeyError('Cannot register {}, not mentioned in docstring/docopt.'.format(command_name))
        if OPTIONS[command_name]:
            command.chosen = func

        return wrapped

    return function_wrap


@command()
def server():
    eventlet.monkey_patch()
    options = parse_options()
    setup_logging('server', logging.DEBUG if options.DEBUG else logging.WARNING)
    app = create_app(options)
    log_messages(app)
    socketio.run(app, host=app.config['HOST'], port=int(app.config['PORT']), debug=app.config['DEBUG'])


@command()
def list_routes():
    output = []
    app = create_app(parse_options())
    app.config['SERVER_NAME'] = 'example.com'
    with app.app_context():
        for rule in app.url_map.iter_rules():

            integer_replaces = {}
            options = {}
            integer = 0
            for arg in rule.arguments:
                options[arg] = str(integer)
                integer_replaces[str(integer)] = "[{0}]".format(arg)
                integer = +1

            methods = ','.join(rule.methods)
            url = flask.url_for(rule.endpoint, **options)
            for integer_replace in integer_replaces:
                url = url.replace(integer_replace, integer_replaces[integer_replace])
            line = urllib.parse.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, url))
            output.append(line)

        for line in sorted(output):
            print(line)


@command()
def celerydev():
    options = parse_options()
    setup_logging('celerydev', logging.DEBUG if options.DEBUG else logging.WARNING)
    app = create_app(options, no_sql=True)
    Logging._setup = True  # Disable Celery from setting up logging, already done in setup_logging().
    with app.app_context():
        hostname = OPTIONS['--name'] if OPTIONS['--name'] else host_format(default_nodename(None))
        worker = celery.Worker(
            hostname=hostname, pool_cls=None, loglevel='WARNING',
            logfile=None,  # node format handled by celery.app.log.setup
            pidfile=node_format(None, hostname),
            statedb=node_format(None, hostname),  # ctx.obj.app.conf.worker_state_db
            no_color=False,
            concurrency=5,
            schedule='/tmp/celery.db',
            beat=True

        )
        worker.start()
        return worker.exitcode


@command()
def celerybeat():
    options = parse_options()
    setup_logging('celerybeat', logging.DEBUG if options.DEBUG else logging.WARNING)
    app = create_app(options, no_sql=True)
    Logging._setup = True
    with app.app_context():
        return celery.Beat(
            logfile=None,
            pidfile=OPTIONS['--pid'],
            schedule=OPTIONS['--schedule']
        ).run()


@command()
def celeryworker():
    options = parse_options()
    setup_logging('celeryworker{}'.format(OPTIONS['--name']), logging.DEBUG if options.DEBUG else logging.WARNING)
    app = create_app(options, no_sql=True)
    Logging._setup = True
    with app.app_context():
        hostname = OPTIONS['--name'] if OPTIONS['--name'] else host_format(default_nodename(None))
        worker = celery.Worker(
            hostname=hostname, pool_cls=None, loglevel='WARNING',
            logfile=None,  # node format handled by celery.app.log.setup
            pidfile=node_format(None, hostname),
            statedb=node_format(None, hostname), #ctx.obj.app.conf.worker_state_db
            no_color=False,
            autoscale='10,1',
            without_gossip=True

        )
        worker.start()
        return worker.exitcode


@command()
def post_install():
    app = create_app(parse_options())
    config_path = os.path.join('/', 'etc', 'tux-control', 'config.yml')

    def run_psql_command(sql):
        subprocess.call(['su', '-c', 'psql -c "{}"'.format(sql), 'postgres'])

    def get_random_password():
        return hashlib.md5(str(random.randint(0, sys.maxsize)).encode('UTF-8')).hexdigest()

    with ConfigParser(Path(config_path)) as config_parser:
        # Generate rabbitmq access info for celery
        celery_broker_url = config_parser.get('CELERY_BROKER_URL')
        if not celery_broker_url:
            celery_broker_username = 'tux_control_celery'
            celery_broker_vhost = 'tux_control_celery'
            celery_broker_password = get_random_password()
            # Create rabbitmq user and vhost
            subprocess.call(['rabbitmqctl', 'add_vhost', celery_broker_vhost])
            subprocess.call(['rabbitmqctl', 'add_user', celery_broker_username, celery_broker_password])
            subprocess.call(['rabbitmqctl', 'set_permissions', '-p', celery_broker_vhost, celery_broker_username, '.*', '.*', '.*'])

            config_parser['CELERY_BROKER_URL'] = 'amqp://{}:{}@127.0.0.1:5672/{}'.format(
                celery_broker_username,
                celery_broker_password,
                celery_broker_vhost
            )

            # We need to set DB config to make stamp work
            app.config['CELERY_BROKER_URL'] = config_parser['CELERY_BROKER_URL']
            config_parser.save()

        # Generate rabbitmq access info for socketio message queue
        socket_io_message_queue = config_parser.get('SOCKET_IO_MESSAGE_QUEUE')
        if not socket_io_message_queue:
            socket_io_message_queue_username = 'tux_control_socketio'
            socket_io_message_queue_vhost = 'tux_control_socketio'
            socket_io_message_queue_password = get_random_password()
            # Create rabbitmq user and vhost
            subprocess.call(['rabbitmqctl', 'add_vhost', socket_io_message_queue_vhost])
            subprocess.call(['rabbitmqctl', 'add_user', socket_io_message_queue_username, socket_io_message_queue_password])
            subprocess.call(
                ['rabbitmqctl', 'set_permissions', '-p', socket_io_message_queue_vhost, socket_io_message_queue_username, '.*', '.*', '.*'])

            config_parser['SOCKET_IO_MESSAGE_QUEUE'] = 'amqp://{}:{}@127.0.0.1:5672/{}'.format(
                socket_io_message_queue_username,
                socket_io_message_queue_password,
                socket_io_message_queue_vhost
            )

            # We need to set DB config to make stamp work
            app.config['SOCKET_IO_MESSAGE_QUEUE'] = config_parser['SOCKET_IO_MESSAGE_QUEUE']
            config_parser.save()

        # Generate database and config if nothing is specified
        sqlalchemy_database_uri = config_parser.get('SQLALCHEMY_DATABASE_URI')
        if not sqlalchemy_database_uri:
            # Create Database
            database_username = 'tux_control'
            database_name = 'tux_control'
            database_password = get_random_password()

            run_psql_command('CREATE USER {} WITH PASSWORD \'{}\';'.format(database_username, database_password))
            run_psql_command('CREATE DATABASE {};'.format(database_name))
            run_psql_command('GRANT ALL PRIVILEGES ON DATABASE {} TO {};'.format(database_name, database_username))
            run_psql_command('GRANT USAGE ON SCHEMA public TO {};'.format(database_username))
            run_psql_command('ALTER DATABASE {} OWNER TO {};'.format(database_name, database_username))

            config_parser['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{}:{}@127.0.0.1/{}'.format(
                database_username,
                database_password,
                database_name
            )

            # We need to set DB config to make stamp work
            app.config['SQLALCHEMY_DATABASE_URI'] = config_parser['SQLALCHEMY_DATABASE_URI']

            config_parser.save()

            # Create empty database
            with app.app_context():
                db.create_all()

            with app.app_context():
                stamp()

        # Generate secret key
        secret_key = config_parser.get('SECRET_KEY')
        if not secret_key:
            app.config['SECRET_KEY'] = config_parser['SECRET_KEY'] = get_random_password()
            config_parser.save()

        # Set port and host
        host = config_parser.get('HOST')
        if not host:
            config_parser['HOST'] = '0.0.0.0'
            config_parser.save()

        port = config_parser.get('PORT')
        if not port:
            config_parser['PORT'] = 80
            config_parser.save()


@command()
def set_user():
    password = OPTIONS['<password>']
    system_user = OPTIONS['<system_user>']
    email = OPTIONS['<email>']

    admin_role_name = 'Admin'

    found_admin_role = Role.query.filter_by(name=admin_role_name).one_or_none()
    if not found_admin_role:
        found_admin_role = Role()
        found_admin_role.name = admin_role_name
        db.session.add(found_admin_role)
        db.session.commit()

    for permission_raw_key, permission_raw_description in collect_permissions().items():
        found_permission = Permission.query.filter_by(identifier=permission_raw_key).one_or_none()
        if not found_permission:
            found_permission = Permission()
            found_permission.identifier = permission_raw_key
        found_permission.name = permission_raw_description
        found_permission.roles += [found_admin_role]
        db.session.add(found_permission)

    db.session.commit()

    found_user = User.query.filter_by(email=email).first()
    new = False
    if not found_user:
        new = True
        found_user = User()
    found_user.set_password(password)
    found_user.email = email
    found_user.system_user = system_user
    found_user.full_name = ''
    found_user.roles = [found_admin_role]

    db.session.add(found_user)
    db.session.commit()

    print('User ID: {} {}.'.format(found_user.id, 'created' if new else 'updated'))


@command()
def user():
    action = OPTIONS['<action>']
    email = OPTIONS['<email>']

    def add(config: dict):
        found_user = User.query.filter_by(email=email).first()
        if found_user:
            raise Exception('Email {} already exists.'.format(email))

        password = input('Password: ')
        if not password:
            raise Exception('No password entered.')

        first_name = input('First name: ')
        if not first_name:
            raise Exception('No first name entered.')

        last_name = input('Last name: ')
        if not last_name:
            raise Exception('No first name entered.')

        system_user = input('System user: ')
        if not system_user:
            raise Exception('No system user entered.')

        admin_role_name = 'Admin'

        found_admin_role = Role.query.filter_by(name=admin_role_name).one_or_none()
        if not found_admin_role:
            found_admin_role = Role()
            found_admin_role.name = admin_role_name
            db.session.add(found_admin_role)
            db.session.commit()

        for permission_raw_key, permission_raw_description in collect_permissions().items():
            found_permission = Permission.query.filter_by(identifier=permission_raw_key).one_or_none()
            if not found_permission:
                found_permission = Permission()
                found_permission.identifier = permission_raw_key
            found_permission.name = permission_raw_description
            found_permission.roles += [found_admin_role]
            db.session.add(found_permission)

        db.session.commit()

        new_user = User()
        new_user.set_password(password)
        new_user.email = email
        new_user.first_name = first_name
        new_user.last_name = last_name
        new_user.system_user = system_user
        new_user.full_name = '{} {}'.format(first_name, last_name)
        new_user.roles = [found_admin_role]

        db.session.add(new_user)
        db.session.commit()

        print('User ID: {} created.'.format(new_user.id))

    def delete(config: dict):
        found_user = User.query.filter_by(email=email).first()
        if not found_user:
            raise Exception('Username {} not found.'.format(email))

        db.session.delete(found_user)
        db.session.commit()

    actions = {
        'add': add,
        'delete': delete
    }

    action_call = actions.get(action)

    if not action_call:
        raise Exception('Unknown action {}'.format(action))

    options = parse_options()
    app = create_app(options)
    with app.app_context():
        action_call(app.config)


@command()
def refresh_package_info():
    setup_logging('refresh_package_info')
    app = create_app(parse_options())
    log = logging.getLogger(__name__)
    with app.app_context():
        keys_exists = []
        for control_package_key, control_package_info in get_control_packages().items():
            keys_exists.append(control_package_key)
            log.info('Refreshing package info for package {}'.format(control_package_key))
            package = refresh_package(control_package_key)
            log.info('Package {} refreshed as ID:{}'.format(control_package_key, package.id))

        # Remove packages not in the list anymore
        for package_to_remove in Package.query.filter(Package.key.notin_(keys_exists)):
            log.info('Removing package {} from cache'.format(package_to_remove.name))
            db.session.delete(package_to_remove)

        db.session.commit()

        package_manger_update.delay()


@command()
def create_all():
    setup_logging('create_all')
    app = create_app(parse_options())
    log = logging.getLogger(__name__)
    with app.app_context():
        tables_before = set(db.engine.table_names())
        db.create_all()
        tables_after = set(db.engine.table_names())
    created_tables = tables_after - tables_before
    for table in created_tables:
        log.info('Created table: {}'.format(table))


@command(name='db')
def _db():
    from flask.cli import FlaskGroup
    cli = FlaskGroup(create_app=lambda: create_app(parse_options()))
    cli.main(args=sys.argv[1:])


def main():
    signal.signal(signal.SIGINT, lambda *_: sys.exit(0))  # Properly handle Control+C
    getattr(command, 'chosen')()  # Execute the function specified by the user.


if __name__ == '__main__':
    main()

