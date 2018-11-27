"""Gets username and password."""

from os.path import exists, expanduser
from base64 import b64decode
from getpass import getpass

from exceptions import GetUsernamePasswordError


def load(prompt=False):
    """Gets username & password from AutoAuth app.
    If not found, raise exceptions.GetUsernamePasswordError.
    
    Derived from george-yu/AutoAuth @ GitHub
    """
    try:
        usr_dat = expanduser(
            '~/Library/Application Support/AutoAuth/usr.dat')
        if not exists(usr_dat):
            raise GetUsernamePasswordError("'usr.dat' not found.")

        try:
            with open(usr_dat) as file:
                username = file.readline().strip()
                password = b64decode(file.readline().strip().encode()).decode()
        except (OSError, IOError) as err:
            raise GetUsernamePasswordError(
                "Error when opening 'usr.dat'") from err

        if not username or not password:
            raise GetUsernamePasswordError(
                "'usr.dat' contains invalid username or password.") 

        return username, password
    except GetUsernamePasswordError:
        username = input('Enter username (e.g. s12345): ').strip()
        password = getpass(
            'Password for %s: ' % username).strip()
