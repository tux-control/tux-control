from tux_control.plugin.validators.IValidator import IValidator


class PatternValidator(IValidator):
    name = 'pattern'
    message = None

    def __init__(self, pattern: str, message: str = 'Please enter valid value.'):
        self.pattern = pattern
        self.message = message

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'pattern': self.pattern,
            'message': self.message
        }
