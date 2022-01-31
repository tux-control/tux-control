from tux_control.tools.IDictify import IDictify


class IValidator(IDictify):

    @property
    def name(self) -> str:
        raise NotImplementedError

    @property
    def message(self) -> str:
        raise NotImplementedError

    def validate(self, value) -> bool:
        raise NotImplementedError