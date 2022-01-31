from tux_control.plugin.validators.PatternValidator import PatternValidator


class EmailValidator(PatternValidator):
    name = 'email'
    message = None

    def __init__(self, message: str = 'Please enter valid email.'):
        self.message = message
        self.pattern = r'(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)'

