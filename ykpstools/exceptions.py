"""All exceptions."""

__all__ = ['LoginError', 'LoginConnectionError', 'WrongUsernameOrPassword',
    'GetUsernamePasswordError', 'GetIPError']

class LoginError(Exception):
    """The most basic ykpstools Exception.
    All errors should inherit from it.
    """
    pass


class LoginConnectionError(LoginError, ConnectionError):
    """Connection error encountered in any step."""
    pass


class WrongUsernameOrPassword(LoginError, ValueError):
    """Username or password provided or loaded is wrong."""
    pass


class GetUsernamePasswordError(LoginError, FileNotFoundError):
    """Cannot retrieve username or password from local 'usr.dat'."""
    pass


class GetIPError(LoginError, OSError):
    """Cannot retrieve IP of machine in local network."""
    pass
