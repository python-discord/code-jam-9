from typing import Generic, TypeVar

from websockets import WebSocketCommonProtocol

T = TypeVar("T")


class Connections(Generic[T]):
    """
    Class for managing WebsocketsCommonProtocol instances

    Records a group of WebsocketsCommonProtocol objects in a dict, keyed to
    usernames. Implements adding and removing users and tracks the most
    recently added and most recently departed users.
    """

    def __init__(self, data: dict = None, user_limit: int = None) -> None:
        """Initialize class"""
        self.data = {} if data is None else data
        self._user_limit = user_limit
        self._user_count = 0

    def __len__(self) -> int:
        """Returns number of current users"""
        return len(self.data)

    def __str__(self) -> str:
        """Returns string representation of class dict"""
        return str(self.data)

    def __repr__(self) -> str:
        """Returns string representation of class dict"""
        return str(self)

    @property
    def user_limit(self) -> None | int:
        """Returns current user limit"""
        return self._user_limit

    @user_limit.setter
    def user_limit(self, value: int) -> None:
        """Sets user limit to a value. Does not perform validation"""
        self._user_limit = value

    @property
    def user_count(self) -> int:
        """
        User count property

        Returns `_user_count`, which contains the number of users before
        at the last update
        """
        return self._user_count

    def update_user_count(self) -> None:
        """Updates user count by checking length of the class dict"""
        self._user_count = len(self)

    @property
    def current_users(self) -> str:
        """Return string of current usernames, formatted for JSON transmission"""
        return str(list(self.data.keys())).replace("'", '"')

    def has_user(self, uname: str) -> bool:
        """Determines whether a username is in use"""
        return uname in self.data.keys()

    def add_user(
        self,
        uname: str,
        value: WebSocketCommonProtocol,
        require_unique=False,
    ) -> None | T:
        """
        Method to add new user with a given username

        Adds a username-WebsocketsCommonProtocol pair to class dict,
        optionally raising an error instead of overwriting an existing user.
        """
        if self.has_user(uname) and require_unique:
            raise KeyError(f"username {uname} already in use")
        self.data[uname] = value
        return self.data

    def remove_user(self, uname: str, raise_error: bool = False) -> None | T:
        """
        User deletion method

        Deletes user by name, optionally raising an error if no user has that username.
        """
        if self.has_user(uname):
            del self.data[uname]
        elif raise_error:
            raise KeyError(f"No user named {uname}")
        return self
