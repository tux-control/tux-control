from typing import Type
from tux_control.plugin.validators.PatternValidator import PatternValidator


class UrlValidator(PatternValidator):
    message = None

    def __init__(self, message: str = 'Please enter valid URL.'):
        self.pattern = r'^(?:http(s)?:\/\/)?[\w.-]+(?:\.[\w\.-]+)+[\w\-\._~:/?#[\]@!\$&\'\(\)\*\+,;=.]+$'
        self.message = message

