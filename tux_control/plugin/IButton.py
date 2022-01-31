
from typing import Callable


class IButton:

    @property
    def title(self) -> str:
        raise NotImplementedError

    @property
    def color(self) -> str:
        raise NotImplementedError

    @property
    def icon(self) -> str:
        raise NotImplementedError

    @property
    def confirmation(self) -> str:
        raise NotImplementedError

    @property
    def hook(self) -> Callable:
        raise NotImplementedError

