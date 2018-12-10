"""Class 'User' that stores its user info and functions."""

__all__ = ['User']
__author__ = 'Thomas Zhu'

import base64
import functools
import getpass
import json
import os
import re
from urllib.parse import urlparse, parse_qs
from urllib3.exceptions import InsecureRequestWarning
import warnings

import requests

from ykpstools.page import (Page, PowerschoolPage, MicrosoftPage,
    PowerschoolLearningPage)
from ykpstools.exceptions import (LoginConnectionError,
    WrongUsernameOrPassword, GetUsernamePasswordError, GetIPError)


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
        usr_dat = os.path.expanduser(
        '~/Library/Application Support/AutoAuth/usr.dat')
        if not os.path.exists(usr_dat):
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

    # @property
    # def IP(self):
    #     """Returns IP address in LAN."""
    #     def _is_valid_IP(IP):
    #         """Internal function. Check if IP is internal IPv4 address."""
    #         if (IP and isinstance(IP, str) and not IP.startswith('127.')
    #             and re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', IP)):
    #             return True
    #         else:
    #             return False
    #     try:
    #         IP = socket.gethostbyname(socket.gethostname())
    #         assert _is_valid_IP(IP)
    #     except (socket.error, AssertionError):
    #         try:
    #             IP = socket.gethostbyname(socket.getfqdn())
    #             assert _is_valid_IP(IP)
    #         except (socket.error, AssertionError):
    #             if sys.platform in {'win32', 'win16', 'dos', 'cygwin'}:
    #                 try:
    #                     ipconfig = subprocess.check_output('ipconfig /all',
    #                         shell=True, stderr=subprocess.DEVNULL).decode()
    #                 except subprocess.CalledProcessError as error:
    #                     raise GetIPError(
    #                         "Can't retrieve IP address.") from error
    #                 else:
    #                     for ipconfig_line in ipconfig.splitlines():
    #                         line = ipconfig_line.strip()
    #                         if re.search(r'[\s^]IP(?:v4)?[\s\:$]', line):
    #                             # 'IP' or 'IPv4'
    #                             IP = line.split()[-1]
    #                             if _is_valid_IP(IP):
    #                                 break
    #                     else:
    #                         raise GetIPError("Can't retrieve IP address.")
    #             elif (sys.platform == 'darwin'
    #                 or sys.platform.startswith('linux')):
    #                 macos_interfaces = ['en0', 'en1']
    #                 linux_interfaces = ['eth0', 'wlan0', 'wifi0', 'eth1',
    #                     'eth2', 'wlan1', 'ath0', 'ath1', 'ppp0']
    #                 if sys.platform == 'darwin':
    #                     interfaces = macos_interfaces + linux_interfaces
    #                 elif sys.platform.startswith('linux'):
    #                     interfaces = linux_interfaces + macos_interfaces
    #                 for interface in interfaces:
    #                     try:
    #                         ifconfig = subprocess.check_output(
    #                             'ifconfig {} | grep "inet "'.format(interface),
    #                             shell=True, stderr=subprocess.DEVNULL).decode()
    #                         IP = ifconfig.splitlines()[0].strip().split()[1]
    #                         assert _is_valid_IP(IP)
    #                     except (subprocess.CalledProcessError,
    #                         AssertionError, IndexError):
    #                         continue
    #                     else:
    #                         break
    #                 else:
    #                     raise GetIPError("Can't retrieve IP address. "
    #                         'Maybe your network is disabled or disconnected?')
    #             else:
    #                 raise GetIPError('Not implemented OS: ' + sys.platform)
    #     if not _is_valid_IP(IP):
    #         raise GetIPError("Can't retrieve IP address.")
    #     else:
    #         return IP

    # @property
    # def MAC(self):
    #     """Returns MAC address."""
    #     MAC = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
    #     return ':'.join([MAC[i:i+2] for i in range(0, 11, 2)])

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

        *args: arguments for self.session.request,
        **kwargs: keyword arguments for self.session.request.
        """
        return Page(self, self.session.request(*args, **kwargs))

    @_connection_error_wrapper
    def get(self, *args, **kwargs):
        """Simple wrapper for
        ykpstools.page.Page(self, self.session.get(*args, **kwargs)).

        *args: arguments for self.session.get,
        **kwargs: keyword arguments for self.session.get.
        """
        return Page(self, self.session.get(*args, **kwargs))

    @_connection_error_wrapper
    def post(self, *args, **kwargs):
        """Simple wrapper for
        ykpstools.page.Page(self, self.session.post(*args, **kwargs)).

        *args: arguments for self.session.post,
        **kwargs: keyword arguments for self.session.post.
        """
        return Page(self, self.session.post(*args, **kwargs))

    def auth(self, updates={}, *args, **kwargs):
        """Logins to YKPS Wi-Fi."""
        ext_portal = self.get('http://1.1.1.1:8000/ext_portal.magi',
            *args, **kwargs)
        # html is like <script>location.replace("url")</script>, hence
        url = re.findall(
            r'''location\.replace\(['"](.*)['"]\);''', ext_portal.text())[0]
        if url == 'http://1.1.1.1:8000/logout.htm':
            return ext_portal
        with warnings.catch_warnings(): # catch InsecureRequestWarning
            warnings.simplefilter('ignore', category=InsecureRequestWarning)
            portal = self.get(url, verify=False)
            credentials = {'userid': self.username, 'passwd': self.password}
            credentials.update(updates)
            submit_auth = portal.submit( # no redirects to make process faster
                updates=credentials, verify=False, allow_redirects=False)
            if submit_auth.response.status_code == 200: # should not happen
                # html is like <script>alert('error')</script>, hence
                raise WrongUsernameOrPassword('From server: ' + re.findall(
                    r'''alert\(['"](.*)['"]\);''', submit_auth.text())[0])
            else:
                return submit_auth

    def powerschool(self):
        """Returns login to Powerschool Page."""
        return PowerschoolPage(self)

    def microsoft(self, redirect_to_ms=None):
        """Returns login to Microsoft Page.
        
        redirect_to_ms: ykpstools.page.Page instance, the page that a login
                        page redirects to for Microsoft Office365 login,
                        defaults to
                        self.get('https://login.microsoftonline.com/').
        """
        return MicrosoftPage(self, redirect_to_ms)

    def powerschool_learning(self):
        """Returns login to Powerschool Learning Page."""
        return PowerschoolLearningPage(self)
