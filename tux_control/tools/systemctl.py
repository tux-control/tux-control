import subprocess


def is_enabled(service: str) -> bool:
    return _systemctl('is-enabled', service)['stdout'].strip() == 'enabled'


def is_active(service: str) -> bool:
    return _systemctl('is-active', service)['stdout'].strip() == 'active'


def is_failed(service: str) -> bool:
    return _systemctl('is-failed', service)['stdout'].strip() == 'failed'


def enable(service: str) -> bool:
    return _systemctl('enable', service)['code'] == 0


def disable(service: str) -> bool:
    return _systemctl('disable', service)['code'] == 0


def start(service: str) -> bool:
    return _systemctl('start', service)['code'] == 0


def stop(service: str) -> bool:
    return _systemctl('stop', service)['code'] == 0


def restart(service: str) -> bool:
    return _systemctl('restart', service)['code'] == 0


def reboot() -> bool:
    return _systemctl('reboot')['code'] == 0


def poweroff() -> bool:
    return _systemctl('poweroff')['code'] == 0


def daemon_reload() -> bool:
    return _systemctl('daemon-reload')['code'] == 0


def _systemctl(command: str, service: str=None) -> dict:
    cmd = ['systemctl', command]
    if service:
        cmd.append(service)

    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    data = p.communicate()
    data = {
        "code": p.returncode,
        "stdout": data[0].decode(),
        "stderr": data[1].rstrip(b'\n').decode()
    }
    return data