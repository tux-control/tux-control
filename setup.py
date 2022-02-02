#!/usr/bin/env python
import os
import sys

from setuptools import setup, find_packages

sys_conf_dir = os.getenv("SYSCONFDIR", "/etc")
lib_dir = os.getenv("LIBDIR", "/usr/lib")


def get_requirements(filename):
    package_list = []
    with open(os.path.join(filename), 'r') as rf:
        for line in rf.readlines():
            if line.startswith('git'):
                git_url, package_name = line.split('#egg=')
                # prefix line with package name
                package_list.append('{} @ {}'.format(package_name, git_url))
            else:
                package_list.append(line)

    return package_list


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
    Programming Language :: Python :: 2
    Programming Language :: Python :: 2.7
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


install_requires = get_requirements('requirements.txt')
if sys.version_info < (3, 0):
    install_requires.append('futures')


extra_files = [
        'templates/*',
        'migrations/alembic.ini',
        'views/*/templates/*',
        'views/*/templates/*/*',
        'static/*'
]

setup(
    name='tux-control',
    version='0.0.10',
    description='Tux Control',
    long_description=open('README.md').read(),
    author='Adam Schubert',
    author_email='adam.schubert@sg1-game.net',
    url='https://gitlab.salamek.cz/sadam/tux-control.git',
    license='GPL-3',
    classifiers=classifiers,
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=install_requires,
    test_suite="tests",
    tests_require=install_requires,
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
