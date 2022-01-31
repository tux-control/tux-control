"""
Bootstrap for use in uwsgi and so
"""

from tux_control.application import create_app, get_config

config = get_config('tux_control.config.Production')
app = create_app(config)