from tux_control.plugin.validators.IValidator import IValidator


class RequiredValidator(IValidator):
    name = 'required'
    message = None

    def __init__(self, message: str = 'This field is required.'):
        self.message = message

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'message': self.message
        }

    def validate(self, value) -> bool:
        return True if value else False
