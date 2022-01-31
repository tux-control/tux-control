from tux_control.models.tux_control import Package


def format_bytes(num, suffix: str='B') -> str:
    """
    Format bytes to human readable string
    @param num:
    @param suffix:
    @return:
    """

    if num is None:
        num = 0

    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)
