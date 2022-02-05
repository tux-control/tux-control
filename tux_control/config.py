from celery.schedules import crontab


class HardCoded(object):
    """Constants used throughout the application.

    All hard coded settings/data that are not actual/official configuration options for Flask, Celery, or their
    extensions goes here.
    """
    ADMINS = ['adam.schubert@sg1-game.net']
    DB_MODELS_IMPORTS = ('tux_control',)  # Like CELERY_IMPORTS in CeleryConfig.
    ENVIRONMENT = property(lambda self: self.__class__.__name__)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SUPPORTED_LANGUAGES = {'cs': 'Čeština', 'en': 'English'}
    LANGUAGE = 'cs'


class CeleryConfig(HardCoded):
    """Configurations used by Celery only."""
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    CELERY_TASK_SOFT_TIME_LIMIT = 20 * 60  # Raise exception if task takes too long.
    CELERY_TASK_TIME_LIMIT = 30 * 60  # Kill worker if task takes way too long.
    CELERY_ACCEPT_CONTENT = ['json']
    CELERY_TASK_ACKS_LATE = True
    CELERY_WORKER_DISABLE_RATE_LIMITS = True
    CELERY_IMPORTS = ('tux_control',)
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_RESULT_EXPIRES = 10 * 60  # Dispose of Celery Beat results after 10 minutes.
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_DEFAULT_QUEUE = 'tux-control'

    CELERY_BEAT_SCHEDULE = {
        'pacman-every-day': dict(task='tux_control.pacman_update', schedule=crontab(day_of_week='1')),
    }


class Config(CeleryConfig):
    """Default Flask configuration inherited by all environments. Use this for development environments."""
    DEBUG = True
    TESTING = False
    SECRET_KEY = "i_don't_want_my_cookies_expiring_while_developing_tux_control"
    CELERY_BROKER_URL = 'amqp://127.0.0.1:5672/tux_control'
    SOCKET_IO_MESSAGE_QUEUE = 'amqp://127.0.0.1:5672/tux_control'
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/tux_control.db'
    PACKAGES_SEARCH_PATH = ['/etc/tux-control/packages', 'etc/tuxcontrol/packages']
    PORT = 5000
    HOST = '0.0.0.0'

    DATA_STORAGE = '/tmp'

    JWT_ERROR_MESSAGE_KEY = 'message'
    JWT_TOKEN_LOCATION = ('headers', 'json', 'query_string')
    JWT_QUERY_STRING_NAME = 'jwt'
    JWT_ACCESS_TOKEN_EXPIRES = False

    PERMISSIONS = {
        'user.read': 'Allows access to users',
        'user.edit': 'Allows modification of users',
        'user.delete': 'Allows deletion of users',

        'role.edit': 'Allows modification of role',
        'role.delete': 'Allows deletion of role',

        'file.edit': 'Allows modification of files',
        'file.read': 'Allows access to files',
        'file.delete': 'Allows deletion of files',
    }


class Testing(Config):
    TESTING = True
    CELERY_ALWAYS_EAGER = True
    CELERY_BROKER_URL = 'amqp://127.0.0.1:5672/tux_control'
    SOCKET_IO_MESSAGE_QUEUE = 'amqp://127.0.0.1:5672/tux_control'


class Production(Config):
    DEBUG = False
    SECRET_KEY = None  # To be overwritten by a YAML file.
    PORT = None  # To be overwritten by a YAML file.
    HOST = None  # To be overwritten by a YAML file.
