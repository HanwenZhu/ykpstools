"""Class 'User' that stores its user info and functions."""

__all__ = ['User']
__author__ = 'Thomas Zhu'

import base64
import functools
import getpass
import os

import requests

from ykpstools.page import (Page, AuthPage, PowerschoolPage, MicrosoftPage,
    PowerschoolLearningPage)
from ykpstools.exceptions import (LoginConnectionError,
    GetUsernamePasswordError)


class User:

    """Class 'User' that stores its user info and functions."""

    def __init__(self, username=None, password=None, *, load=True,
        prompt=False, session_args=(), session_kwargs={}):
        """Initialize a User.

        username=None: str, user's username, defaults to load or prompt,
        password=None: str, user's password, defaults to load or prompt,
        load=True: bool, try load username and password from local AutoAuth,
        prompt=False: bool, prompt for username and password if can't load,
        session_args=(): tuple, arguments for requests.Session,
        session_kwargs={}: dict, keyword arguments for requests.Session.
        """
        self.session = requests.Session(*session_args, **session_kwargs)
        self.session.headers.update(
            {'User-Agent': ' '.join((
                'Mozilla/5.0 (compatible; Intel Mac OS X 10_13_6)',
                'AppleWebKit/537.36 (KHTML, like Gecko)',
                'Chrome/70.0.3538.110',
                'Safari/537.36',
        ))})
        if username is not None and password is not None:
            self.username, self.password = username, password
        else:
            if load:
                if prompt:
                    try:
                        self.username, self.password = self._load()
                    except GetUsernamePasswordError:
                        self.username, self.password = self._prompt()
                else:
                    self.username, self.password = self._load()
            else:
                if prompt:
                    self.username, self.password = self._prompt()
                else:
                    raise GetUsernamePasswordError(
                        'Username or password unprovided, while not allowed'
                        'to load or prompt for username or password.')

    @staticmethod
    def _load():
        """Internal function.
        Derived from: https://github.com/yu-george/AutoAuth-YKPS/
        """
        usr_dat = '~/Library/Application Support/AutoAuth/usr.dat'
        usr_dat = os.path.expanduser(usr_dat)
        if not os.path.isfile(usr_dat):
            raise GetUsernamePasswordError("'usr.dat' not found.")
        try:
            with open(usr_dat) as file:
                username = file.readline().strip()
                password = base64.b64decode(
                    file.readline().strip().encode()).decode()
        except (OSError, IOError) as error:
            raise GetUsernamePasswordError(
                "Error when opening 'usr.dat'") from error
        if not username or not password:
            raise GetUsernamePasswordError(
                "'usr.dat' contains invalid username or password.")
        return username, password

    @staticmethod
    def _prompt():
        """Internal function. Prompt inline for username and password."""
        username = input('Enter username (e.g. s12345): ').strip()
        password = getpass.getpass(
            'Password for {}: '.format(username)).strip()
        return username, password

    def _connection_error_wrapper(function):
        """Internal decorator. Raise LoginConnectionError if can't connect."""
        @functools.wraps(function)
        def wrapped_function(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except requests.exceptions.RequestException as error:
                raise LoginConnectionError(str(error)) from error
        return wrapped_function

    @_connection_error_wrapper
    def request(self, *args, **kwargs):
        """Simple wrapper for
        ykpstools.page.Page(self, self.session.request(*args, **kwargs)).
        """
        return Page(self, self.session.request(*args, **kwargs))

    @_connection_error_wrapper
    def get(self, *args, **kwargs):
        """Simple wrapper for
        ykpstools.page.Page(self, self.session.get(*args, **kwargs)).
        """
        return Page(self, self.session.get(*args, **kwargs))

    @_connection_error_wrapper
    def post(self, *args, **kwargs):
        """Simple wrapper for
        ykpstools.page.Page(self, self.session.post(*args, **kwargs)).
        """
        return Page(self, self.session.post(*args, **kwargs))

    del _connection_error_wrapper

    def auth(self, *args, **kwargs):
        """Simple wrapper for
        ykpstools.page.AuthPage(self, *args, **kwargs).
        """
        return AuthPage(self, *args, **kwargs)

    def powerschool(self, *args, **kwargs):
        """Simple wrapper for
        ykpstools.page.PowerschoolPage(self, *args, **kwargs).
        """
        return PowerschoolPage(self, *args, **kwargs)

    def microsoft(self, *args, **kwargs):
        """Simple wrapper for
        ykpstools.page.MicrosoftPage(self, *args, **kwargs).
        """
        return MicrosoftPage(self, *args, **kwargs)

    def powerschool_learning(self, *args, **kwargs):
        """Simple wrapper for
        ykpstools.page.PowerschoolLearningPage(self, *args, **kwargs).
        """
        return PowerschoolLearningPage(self, *args, **kwargs)
