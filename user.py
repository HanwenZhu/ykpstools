"""The main class 'User'."""

import requests

from webutils import get_IP, get_MAC, set_up_session
from creds import load
from wifilogin import auth
import logins


class User:

    """The class 'User' that stores its user info and functions."""

    def __init__(self, username=None, password=None,
        session=requests.Session(), prompt=False,
        session_args=(), session_kwargs={}):
        """Initialize a User.

        username_password: (username: str, password: str), defaults to
                           creds.load()
        """
        self.session = set_up_session(*session_args, **session_kwargs)
        if username is None or password is None:
            self.username, self.password = load(prompt)
        else:
            self.username, self.password = username_password
        self.IP = get_IP()
        self.MAC = get_MAC()

    def wifi_auth(self):
        """Logins to YKPS Wi-Fi."""
        return auth(
            self.username, self.password, session=self.session,
            self.IP, self.MAC)

    def ps_login(self):
        """Returns login to Powerschool response."""
        return logins.ps_login(
            self.username, self.password, session=self.session)

    def ms_login(self):
        """Returns login to Microsoft response."""
        return logins.ms_login(
            self.username, self.password, session=self.session)

    def psl_login(self):
        """Returns login to Powerschool Learning response."""
        return logins.psl_login(
            self.username, self.password, session=self.session)

    def office_login(self):
        """Returns login to Office response."""
        return logins.office_login(
            self.username, self.password, session=self.session)
