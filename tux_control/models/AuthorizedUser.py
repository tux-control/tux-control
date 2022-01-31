import datetime
from tux_control.models.tux_control import User
from tux_control.tools.IDictify import IDictify


class AuthorizedUser(IDictify):
    access_token: str = None
    access_token_expires: datetime.datetime = None
    refresh_token: str = None
    refresh_token_expires: datetime.datetime = None
    user: User = None

    def __init__(self, access_token: str = None, access_token_expires: datetime.datetime = None, refresh_token: str = None, refresh_token_expires: datetime.datetime = None, user: User = None):
        self.access_token = access_token
        self.access_token_expires = access_token_expires
        self.refresh_token = refresh_token
        self.refresh_token_expires = refresh_token_expires
        self.user = user

    def to_dict(self) -> dict:
        return {
            'access_token': self.access_token,
            'access_token_expires': self.access_token_expires,
            'refresh_token': self.refresh_token,
            'refresh_token_expires': self.refresh_token_expires,
            'user': self.user
        }