from tux_control.plugin.validators.IValidator import IValidator


class MinValidator(IValidator):
    name = 'min'
    message = None

    def __init__(self, min_value: int, message: str = 'Please enter valid value.'):
        self.min_value = min_value
        self.message = message

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'min_value': self.min_value,
            'message': self.message
        }

    def validate(self, value) -> bool:
        return int(value) > self.min_value
