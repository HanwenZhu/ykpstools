"""All exceptions."""

__all__ = ['Error', 'LoginConnectionError', 'WrongUsernameOrPassword',
    'GetUsernamePasswordError', 'GetIPError']
__author__ = 'Thomas Zhu'


class Error(Exception):

    """Basic ykpstools exception that all errors should inherit from."""

    pass


class LoginConnectionError(Error, ConnectionError):

    """Connection error encountered in any step."""

    pass


class WrongUsernameOrPassword(Error, ValueError):

    """The username or password submitted is wrong."""

    def __init__(self, msg='The username or password submitted is wrong.',
        *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class GetUsernamePasswordError(Error, FileNotFoundError, IOError, ValueError):

    """Cannot retrieve username or password from local 'usr.dat'."""

    pass


class GetIPError(Error, OSError, NotImplementedError):

    """Cannot retrieve IP address."""

    pass
