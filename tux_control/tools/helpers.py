import os
import datetime
import multiprocessing
import netifaces
import hashlib
import math
import psutil
from typing import Generator


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


def get_cpu_usage():
    return psutil.cpu_percent(percpu=True)


def get_ram_usage():
    return psutil.virtual_memory()


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


def get_interface_ip_address(if_name: str, net_type: int=netifaces.AF_INET) -> str:
    addrs = netifaces.ifaddresses(if_name)
    return addrs[net_type] if net_type in addrs else None


def get_interface_list() -> list:
    return netifaces.interfaces()


def get_binding_ips() -> dict:
    binds = {
        '0.0.0.0': 'Everywhere IPv4',
        '::': 'Everywhere IPv6',
        '127.0.0.1': 'Localhost IPv4',
        '::1': 'Localhost IPv6'
    }

    for interface in get_interface_list():
        ipv4_addresses = get_interface_ip_address(interface)
        ipv6_addresses = get_interface_ip_address(interface, netifaces.AF_INET6)
        if ipv4_addresses:
            ip_address_ipv4 = ipv4_addresses[0]['addr']
            binds[ip_address_ipv4] = '{} ({})'.format(interface, ip_address_ipv4)

        if ipv6_addresses:
            ip_address_ipv6 = ipv6_addresses[0]['addr']
            binds[ip_address_ipv6] = '{} ({})'.format(interface, ip_address_ipv6)

    return binds


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


def get_interfaces_ip() -> list:
    interface_list = []
    for iface in get_interface_list():
        if iface == 'lo':
            continue
        interface_list.append({
            'name': iface,
            'inet4': get_interface_ip_address(iface, netifaces.AF_INET),
            'inet6': get_interface_ip_address(iface, netifaces.AF_INET6)
        })

    return interface_list


def get_number_of_cores() -> int:
    return multiprocessing.cpu_count()


