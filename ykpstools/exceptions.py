"""All exceptions."""

__all__ = ['LoginError', 'LoginConnectionError', 'WrongUsernameOrPassword',
    'GetUsernamePasswordError', 'GetIPError']

class LoginError(Exception):
    pass


class LoginConnectionError(LoginError, ConnectionError):
    pass


class WrongUsernameOrPassword(LoginError, ValueError):
    pass


class GetUsernamePasswordError(LoginError, FileNotFoundError):
    pass


class GetIPError(LoginError, OSError):
    pass
