"""Gets username and password."""

__all__ = ['load']

from os.path import exists, expanduser
from base64 import b64decode
from getpass import getpass

from .exceptions import GetUsernamePasswordError


def load(prompt=False):
    """Gets username & password from AutoAuth app.
    If not found, raise exceptions.GetUsernamePasswordError.
    
    Derived from george-yu/AutoAuth @ GitHub

    prompt: bool, prompt user for password in shell if encounters error
    """
    if not prompt:
        return _load()
    else:
        try:
            return _load()
        except GetUsernamePasswordError as error:
            return _prompt()


def _load():
    """Internal function."""
    usr_dat = expanduser(
    '~/Library/Application Support/AutoAuth/usr.dat')
    if not exists(usr_dat):
        raise GetUsernamePasswordError("'usr.dat' not found.")

    try:
        with open(usr_dat) as file:
            username = file.readline().strip()
            password = b64decode(file.readline().strip().encode()).decode()
    except (OSError, IOError) as error:
        raise GetUsernamePasswordError(
            "Error when opening 'usr.dat'") from error

    if not username or not password:
        raise GetUsernamePasswordError(
            "'usr.dat' contains invalid username or password.") 

    return username, password


def _prompt():
    """Internal function."""
    username = input('Enter username (e.g. s12345): ').strip()
    password = getpass(
        'Password for %s: ' % username).strip()
    return username, password
