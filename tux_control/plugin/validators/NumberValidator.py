import re
from typing import Type, Union
from tux_control.plugin.validators.PatternValidator import PatternValidator


class NumberValidator(PatternValidator):
    message = None

    def __init__(self, number_type: Type[Union[int, float]] = int, message: str = 'Please enter valid number.'):
        self.pattern = r'^(?:-|)\d+$' if number_type is int else r'^(?:-|)(?:\d+.\d+|\d+)$'
        self.message = message

    def validate(self, value) -> bool:
        if re.match(self.pattern, value):
            return True
        return False