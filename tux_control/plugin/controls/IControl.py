class IControl:

    @property
    def html_type(self) -> str:
        raise NotImplementedError

    @property
    def placeholder(self) -> str:
        raise NotImplementedError

    @staticmethod
    def from_dict(data: dict) -> 'IControl':
        raise NotImplementedError
