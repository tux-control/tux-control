

import json
import hashlib
from logging import getLogger
from flask_celery import single_instance
from flask_babel import gettext
from tux_control.extensions import celery, db, socketio, package_manager
from tux_control.models.tux_control import Update, PackageUpdate, Package
from tux_control.tools.packages import get_control_packages, refresh_package
from tux_control.tools import systemctl

LOG = getLogger(__name__)
THROTTLE = 1 * 60 * 60


@celery.task(bind=True)
@single_instance
def package_manger_upgrade(self) -> None:
    socketio.emit('package_manager_upgrade_progress', {
        'total': 1,
        'processed': 1,
        'message': gettext('Refreshing repositories...')
    })
    package_manager.refresh()
    socketio.emit('package_manager_upgrade_progress', {
        'total': 1,
        'processed': 1,
        'message': gettext('Refreshing repositories done')
    })

    try:
        update = Update.query.filter(Update.is_canceled == False, Update.is_done == False).first()
        if update:
            restart_services = []
            packages_count = update.package_updates.count()
            processed = 0
            for package_update in update.package_updates:
                socketio.emit('package_manager_upgrade_progress', {
                    'total': packages_count,
                    'processed': processed,
                    'message': package_update.package.name,
                    'name': package_update.package.name
                })

                if package_update.package.is_control_services_restart:
                    # If I'M upgraded package, disable service restart in post_install script and restart after it is done
                    package_manager.upgrade([package_update.package.key], env={'PREVENT_RESTART': 'yes'})
                    restart_services.extend([i.name for i in package_update.package.package_services])
                else:
                    package_manager.upgrade([package_update.package.key])
                refresh_package(package_update.package.key)

                processed += 1

                socketio.emit('package_manager_upgrade_progress', {
                    'total': packages_count,
                    'processed': processed,
                    'message': package_update.package.name,
                    'name': package_update.package.name
                })

            update.is_done = True
            db.session.add(update)
            db.session.commit()

            for service_name in restart_services:
                systemctl.restart(service_name)
    except Exception as e:
        socketio.emit('package_manager_update_progress', {
            'total': 1,
            'processed': 1,
            'message': gettext('Upgrade failed: %(message)s', message=str(e))
        })
        raise e
    finally:
        socketio.emit('package_manager_upgrade_done')


@celery.task(bind=True, soft_time_limit=120)
@single_instance
def package_manger_update(self, task_id: str=None) -> None:
    control_packages = get_control_packages()
    socketio.emit('package_manager_update_progress', {
        'total': 1,
        'processed': 1,
        'message': gettext('Refreshing repositories...')
    })
    package_manager.refresh()
    socketio.emit('package_manager_update_progress', {
        'total': 1,
        'processed': 1,
        'message': gettext('Refreshing repositories done')
    })
    try:
        updatable = package_manager.get_updatable()
        if len(list(set([u.name for u in updatable]).intersection(control_packages.keys()))):

            hash_object = hashlib.sha256(json.dumps([u.to_dict() for u in updatable]).encode('UTF-8'))
            identifier = hash_object.hexdigest()

            # cancel previous update
            for to_cancel in Update.query.filter(Update.is_canceled == False, Update.identifier != identifier):
                to_cancel.is_canceled = True
                db.session.add(to_cancel)
            db.session.commit()

            update = Update.query.filter(Update.identifier == identifier).first()
            if not update:

                update = Update()
                update.identifier = identifier

                for package_info in updatable:
                    if package_info.name in control_packages.keys():  # Update only tux packages for now
                        package = Package.query.filter_by(key=package_info.name).first()
                        if not package:
                            raise Exception('Package name {} not found in Package'.format(package_info.name))
                        package_update = PackageUpdate()
                        package_update.package = package
                        package_update.version_from = package_info.from_version
                        package_update.version_to = package_info.to_version
    
                        update.package_updates.append(package_update)

            update.is_canceled = False
            update.is_done = False

            db.session.add(update)
            db.session.commit()
    except Exception as e:
        socketio.emit('package_manager_update_progress', {
            'total': 1,
            'processed': 1,
            'message': gettext('Update failed: %(message)s', message=str(e))
        })
        raise e
    finally:
        socketio.emit('package_manager_update_done')


@celery.task(bind=True)
@single_instance
def package_manager_install(self, package_info: dict) -> None:
    socketio.emit('package_manager_install_progress', {
        'total': 1,
        'processed': 1,
        'message': gettext('Refreshing repositories...')
    })
    package_manager.refresh()
    socketio.emit('package_manager_install_progress', {
        'total': 1,
        'processed': 1,
        'message': gettext('Refreshing repositories done')
    })

    try:
        packages_info_old = package_info['old']
        packages_info_new = package_info['new']

        packages_process = {}

        changes = 0
        for key, package_info_new in packages_info_new.items():
            if package_info_new != packages_info_old[key]:
                changes += 1

                packages_process[key] = package_info_new

        processed = 0
        for package_name, install in packages_process.items():
            if package_name not in get_control_packages().keys():
                raise Exception('Not in allowed packages!')

            if install:
                text = 'Installing %(package_name)s'
            else:
                text = 'Removing %(package_name)s'

            socketio.emit('package_manager_install_progress', {
                'total': changes,
                'processed': processed,
                'message': gettext(text, package_name=package_name),
                'name': package_name
            })

            if install:
                package_manager.install([package_name])
            else:
                package_manager.remove([package_name])

            refresh_package(package_name)

            processed += 1

            socketio.emit('package_manager_install_progress', {
                'total': changes,
                'processed': processed,
                'message': gettext(text, package_name=package_name),
                'name': package_name
            })
    except Exception as e:
        socketio.emit('package_manager_install_progress', {
            'total': 1,
            'processed': 1,
            'message': gettext('Install failed: %(message)s', message=str(e))
        })
        raise e
    finally:
        socketio.emit('package_manager_install_done')


@celery.task(bind=True, soft_time_limit=120)
def service_restart(self, service_name: str) -> None:
    status = systemctl.restart(service_name)

    socketio.emit('service_restart', {'name': service_name, 'status': status})


@celery.task(bind=True, soft_time_limit=120)
def service_start(self, service_name: str) -> None:
    status = systemctl.start(service_name)

    socketio.emit('service_start', {'name': service_name, 'status': status})


@celery.task(bind=True, soft_time_limit=120)
def service_stop(self, service_name: str) -> None:
    status = systemctl.stop(service_name)

    socketio.emit('service_stop', {'name': service_name, 'status': status})