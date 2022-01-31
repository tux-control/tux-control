from tux_control.plugin.validators.IValidator import IValidator


class MaxValidator(IValidator):
    name = 'max'
    message = None

    def __init__(self, max_value: int, message: str = 'Please enter valid value.'):
        self.max_value = max_value
        self.message = message

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'max_value': self.max_value,
            'message': self.message
        }

    def validate(self, value) -> bool:
        return int(value) < self.max_value
