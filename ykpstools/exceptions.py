"""All exceptions."""

__all__ = ['Error', 'LoginConnectionError', 'WrongUsernameOrPassword',
    'GetUsernamePasswordError', 'GetIPError']
__author__ = 'Thomas Zhu'

class Error(Exception):

    """The most basic ykpstools Exception.
    All errors should inherit from it.
    """

    pass


class LoginConnectionError(Error, ConnectionError):

    """Connection error encountered in any step."""

    pass


class WrongUsernameOrPassword(Error, ValueError):

    """Username or password provided or loaded is wrong."""

    def __init__(self,
        message='Username or password provided or loaded is wrong.'):
        super().__init__(message)


class GetUsernamePasswordError(Error, FileNotFoundError, IOError, ValueError):

    """Cannot retrieve username or password from local 'usr.dat'."""

    pass


class GetIPError(Error, OSError, NotImplementedError):

    """Cannot retrieve IP address."""

    pass
