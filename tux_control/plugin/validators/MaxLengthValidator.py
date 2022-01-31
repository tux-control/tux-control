from tux_control.plugin.validators.IValidator import IValidator


class MaxLengthValidator(IValidator):
    name = 'maxlength'
    message = None

    def __init__(self, max_length: int, message: str = 'Please enter string with valid length.'):
        self.max_length = max_length
        self.message = message

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'max_length': self.max_length,
            'message': self.message
        }

    def validate(self, value) -> bool:
        return len(value) < self.max_length

