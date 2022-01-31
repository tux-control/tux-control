import datetime
from yaml import load, SafeLoader
import os
import flask
import glob

from tux_control.models.tux_control import Package, PackageService
from tux_control.extensions import db, package_manager
from tux_control.tools.systemctl import is_enabled, is_active, is_failed


def get_control_packages() -> dict:
    packages = {}
    for config_path in flask.current_app.config.get('PACKAGES_SEARCH_PATH', []):
        for config_file in glob.glob(os.path.join(config_path, '*.yml')):
            package_name = os.path.splitext(os.path.basename(config_file))[0]
            with open(config_file, 'r') as f:
                packages[package_name] = load(f, Loader=SafeLoader)

    return packages


def get_package_config(package: Package) -> dict:
    try:
        with open(package.config_path, 'r') as f:
            return load(f, Loader=SafeLoader)
    except FileNotFoundError:
        return {}


def refresh_package(package_name: str) -> Package:
    control_packages = get_control_packages()
    package_info = control_packages[package_name]
    package = Package.query.filter_by(key=package_name).first()
    if not package:
        package = Package()
        package.name = package_info['name']
        package.key = package_name

    package.config_path = package_info.get('config_path')
    package.endpoint = package_info.get('endpoint')

    package.is_installed = package_manager.is_installed(package.key)
    try:
        package.info = package_manager.get_info(package.key)
    except Exception:
        package.info = None
    package.is_control_services_restart = package_info.get('control_services_restart', False)

    db.session.add(package)

    for position, service_name in enumerate(package_info['services'], start=1):
        package_service = PackageService.query.filter_by(package=package, name=service_name).first()
        if not package_service:
            package_service = PackageService()
            package_service.package = package
            package_service.name = service_name
        package_service.is_enabled = is_enabled(service_name)
        package_service.is_active = is_active(service_name)
        package_service.is_failed = is_failed(service_name)
        package_service.position = position
        db.session.add(package_service)

    db.session.commit()

    return package
