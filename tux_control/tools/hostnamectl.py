import subprocess


def get_hostname() -> str:
    return _hostnamectl('--static')['stdout']


def set_hostname(hostname: str) -> bool:
    return _hostnamectl('set-hostname', hostname)['code'] == 0


def _hostnamectl(command: str, value: str=None) -> dict:
    cmd = ['hostnamectl', command]
    if value:
        cmd.append(value)
    p = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    data = p.communicate()
    data = {
        "code": p.returncode,
        "stdout": data[0].decode(),
        "stderr": data[1].rstrip(b'\n').decode()
    }
    return data