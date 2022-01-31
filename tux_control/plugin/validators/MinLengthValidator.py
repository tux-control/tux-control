from tux_control.plugin.validators.IValidator import IValidator


class MinLengthValidator(IValidator):
    name = 'minlength'
    message = None

    def __init__(self, min_length: int, message: str = 'Please enter string with valid length.'):
        self.min_length = min_length
        self.message = message

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'min_length': self.min_length,
            'message': self.message
        }

    def validate(self, value) -> bool:
        return len(value) > self.min_length
