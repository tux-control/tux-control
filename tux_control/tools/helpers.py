import os
import datetime
import multiprocessing
import hashlib


def get_hash(content: bytes, length: int=32) -> str:
    return hashlib.md5(content).hexdigest()[:length]


def get_mount_info(mount_path: str) -> dict:
    """
    Gets mount info
    @param mount_path:
    @return:
    """
    ret = {}
    try:
        statvfs = os.statvfs(mount_path)
        ret['size'] = statvfs.f_frsize * statvfs.f_blocks
        ret['free_reserved'] = statvfs.f_frsize * statvfs.f_bfree
        ret['free'] = statvfs.f_frsize * statvfs.f_bavail
    except Exception:
        ret['size'] = 0
        ret['free_reserved'] = 0
        ret['free'] = 0

    return ret


def directory_size(source: str) -> int:
    """
    Returns size of directory
    @param source:  path to directory
    @return:
    """
    total_size = os.path.getsize(source)
    for item in os.listdir(source):
        itempath = os.path.join(source, item)
        if os.path.isfile(itempath):
            total_size += os.path.getsize(itempath)
        elif os.path.isdir(itempath):
            total_size += directory_size(itempath)
    return total_size


def get_uptime() -> str:
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return str(datetime.timedelta(seconds=uptime_seconds))


def set_needs_reboot(needs_reboot: bool=True) -> None:
    if needs_reboot:
        with open('/tmp/tux-control-needs-reboot.lock', 'w') as f:
            f.write('True')
    else:
        try:
            os.remove('/tmp/tux-control-needs-reboot.lock')
        except FileNotFoundError:
            pass
        except Exception:
            raise


def is_reboot_needed() -> bool:
    try:
        with open('/tmp/tux-control-needs-reboot.lock', 'r') as f:
            return f.read() == 'True'
    except FileNotFoundError:
        return False
    except Exception:
        raise


def get_number_of_cores() -> int:
    return multiprocessing.cpu_count()


