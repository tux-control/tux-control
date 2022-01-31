from tux_control.plugin.controls.Text import Text


class Number(Text):
    html_type = 'number'
    min_value = None
    max_value = None

    def __init__(self, placeholder: str = None, min_value: int = None, max_value: int = None, step: float = None):
        super().__init__(
            placeholder
        )
        self.min_value = min_value
        self.max_value = max_value
        self.step = step

    def to_dict(self) -> dict:
        parent_dict = super(Number, self).to_dict()
        parent_dict['min'] = self.min_value
        parent_dict['max'] = self.max_value
        parent_dict['step'] = self.step
        return parent_dict

    @staticmethod
    def from_dict(data: dict) -> 'Number':
        return Number(
            data.get('placeholder'),
            data.get('min'),
            data.get('max'),
            data.get('step'),
        )