#!/usr/bin/env python
import os
import sys

from setuptools import setup, find_packages

sys_conf_dir = os.getenv("SYSCONFDIR", "/etc")
lib_dir = os.getenv("LIBDIR", "/usr/lib")


def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths


classes = """
    Development Status :: 4 - Beta
    Intended Audience :: Developers
    Programming Language :: Python
    Programming Language :: Python :: 3
    Programming Language :: Python :: 3.3
    Programming Language :: Python :: 3.4
    Programming Language :: Python :: 3.5
    Programming Language :: Python :: 3.6
    Programming Language :: Python :: Implementation :: CPython
    Programming Language :: Python :: Implementation :: PyPy
    Operating System :: OS Independent
"""
classifiers = [s.strip() for s in classes.split('\n') if s]


extra_files = [
        'templates/*',
        'migrations/alembic.ini',
        'views/*/templates/*',
        'views/*/templates/*/*',
        'static/**/*'
]

setup(
    name='tux-control',
    version='0.1.3',
    description='Tux Control',
    long_description=open('README.md').read(),
    author='Adam Schubert',
    author_email='adam.schubert@sg1-game.net',
    url='https://gitlab.salamek.cz/sadam/tux-control.git',
    license='GPL-3',
    classifiers=classifiers,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'flask>=2.0.0,~=2.2.2',
        'flask-socketio~=5.3.2',
        'python-socketio~=5.7.2',  # Remove old version from my repository if this works
        'Flask-Babel>=2.0.0',
        'flask-migrate>=2.6.0,~=4.0.0',
        'python-magic~=0.4',
        'pyyaml~=6.0.1',
        'docopt~=0.6.2',
        'celery~=5.2.0',
        'Flask-Celery-Tools',
        'flask-sqlalchemy>=2.5.1,~=3.0.3',
        'flask-jwt-extended~=4.4.4',  # Remove old version from my repository if this works
        'file-thumbnailer[pdf]==0.0.9',
        'eventlet',
        'setuptools',
        'flask-cors',
        'psycopg2-binary~=2.9.5',
        'markupsafe>=2.0.1',
        'sqlalchemy~=1.4.46',
    ],
    test_suite="tests",
    tests_require=[
        'tox'
    ],
    package_data={'tux_control': extra_files},
    entry_points={
        'console_scripts': [
            'tux-control = tux_control.__main__:main',
        ],
    },
    data_files=[
        (os.path.join(lib_dir, 'systemd', 'system'), [
            'lib/systemd/system/tux-control.service',
            'lib/systemd/system/tux-control_celeryworker.service',
            'lib/systemd/system/tux-control_celerybeat.service',
        ]),
        (os.path.join(sys_conf_dir, 'tux-control'), [
            'etc/tux-control/config.yml',
        ])
    ]
)
