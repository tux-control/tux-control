

def main():
    """Entrypoint to the ``celery`` umbrella command."""
    from tux_control.bin.tux_control import main as _main
    _main()


if __name__ == '__main__':  # pragma: no cover
    main()