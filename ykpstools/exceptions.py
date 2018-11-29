"""All exceptions."""

class YKPSLoginError(Exception):
    pass


class WrongUsernameOrPassword(YKPSLoginError, ConnectionError, ValueError):
    pass


class GetUsernamePasswordError(YKPSLoginError, FileNotFoundError):
    pass


class GetIPError(YKPSLoginError, OSError):
    pass
