import subprocess
import re


def time() -> dict:
    first_line = _systemd_analyze('time')['stdout'].split('\n')[0]
    found = re.search('([-+]?[0-9]*\.?[0-9]+)s.+?([-+]?[0-9]*\.?[0-9]+)s.+?([-+]?[0-9]*\.?[0-9]+)s', first_line)
    kernel, userspace, total = found.groups()

    # @TODO i dont know how to find last shutdown duration... lets assume it is halve of the boot time...
    shutdown = float(total) / 2
    return {
        'boot': {
            'kernel': float(kernel),
            'userspace': float(userspace),
            'total': float(total)
        },
        'shutdown': {
            'total': shutdown
        },
        'total': float(total) + shutdown
    }


def _systemd_analyze(command: str, service: str=None) -> dict:
    cmd = ['systemd-analyze', command]
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