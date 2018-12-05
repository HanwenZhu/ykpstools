"""Class 'User' that stores its user info and functions."""

__all__ = ['User']
__author__ = 'Thomas Zhu'

import base64
import functools
import getpass
import hashlib
import hmac
import json
import os
import re
import socket
import subprocess
import sys
from urllib.parse import urlparse, parse_qs
from urllib3.exceptions import InsecureRequestWarning
import uuid
import warnings

import requests

from .page import Page
from .exceptions import (LoginConnectionError, WrongUsernameOrPassword,
    GetUsernamePasswordError, GetIPError)


class User:

    """Class 'User' that stores its user info and functions."""

    def __init__(self, username=None, password=None, load=True,
        prompt=False, session_args=(), session_kwargs={}):
        """Initialize a User.

        username=None: str, user's username, defaults to load or prompt,
        password=None: str, user's password, defaults to load or prompt,
        load=True: bool, try load username and password from local AutoAuth,
        prompt=False: bool, prompt for username and password if can't load,
        session_args: tuple, arguments for requests.Session,
        session_kwargs: dict, keyword arguments for requests.Session.
        """
        self.session = requests.Session(*session_args, **session_kwargs)
        self.session.headers.update(
            {'User-Agent': ' '.join((
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6)',
                'AppleWebKit/537.36 (KHTML, like Gecko)',
                'Chrome/69.0.3497.100',
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
        self.IP = self._get_IP()
        self.MAC = self._get_MAC()

    def _load(self):
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

    def _prompt(self):
        """Internal function. Prompt inline for username and password."""
        username = input('Enter username (e.g. s12345): ').strip()
        password = getpass.getpass(
            'Password for {}: '.format(username)).strip()
        return username, password

    def _is_valid_IP(self, IP):
        """Internal function. Check if IP is valid internal IPv4 address."""
        if (IP and isinstance(IP, str) and not IP.startswith('127.')
            and re.match(r'\d{1-3}\.\d{1-3}\.\d{1-3}\.\d{1-3}', IP)):
            return True
        else:
            return False

    def _get_IP(self):
        """Internal function. Returns IP address in LAN."""
        try:
            IP = socket.gethostbyname(socket.gethostname())
            assert self._is_valid_IP(IP)
        except (socket.error, AssertionError):
            try:
                IP = socket.gethostbyname(socket.getfqdn())
                assert self._is_valid_IP(IP)
            except (socket.error, AssertionError):
                if sys.platform in {'win32', 'win16', 'dos', 'cygwin'}:
                    try:
                        ipconfig = str(subprocess.check_output('ipconfig /all',
                            shell=True)) # outputs bytes, hence 'str()'
                    except subprocess.CalledProcessError as error:
                        raise GetIPError(
                            "Can't retrieve IP address.") from error
                    else:
                        for ipconfig_line in ipconfig.splitlines():
                            line = ipconfig_line.strip()
                            if re.search(r'[\s^]IP(?:v4)?[\s\:$]', line):
                                # 'IP' or 'IPv4'
                                IP = line[-1]
                                if self._is_valid_IP(IP):
                                    break
                        else:
                            raise GetIPError("Can't retrieve IP address.")
                elif (sys.platform == 'darwin'
                    or sys.platform.startswith('linux')):
                    macos_interfaces = ['en0', 'en1']
                    linux_interfaces = ['eth0', 'wlan0', 'wifi0', 'eth1',
                        'eth2', 'wlan1', 'ath0', 'ath1', 'ppp0']
                    if sys.platform == 'darwin':
                        interfaces = macos_interfaces + linux_interfaces
                    elif sys.platform.startswith('linux'):
                        interfaces = linux_interfaces + macos_interfaces
                    for interface in interfaces:
                        try:
                            ifconfig = str(subprocess.check_output(
                                'ifconfig {} | grep "inet "'.format(interface),
                                shell=True)) # outputs bytes, hence 'str()'
                            IP = ifconfig.splitlines()[0].strip().split()[1]
                            assert self._is_valid_IP(IP)
                        except (subprocess.CalledProcessError, AssertionError):
                            continue
                        else:
                            break
                    else:
                        raise GetIPError("Can't retrieve IP address.")
                else:
                    raise GetIPError('Not implemented OS: ' + sys.platform)
        if not self._is_valid_IP(IP):
            raise GetIPError("Can't retrieve IP address.")
        else:
            return IP

    def _get_MAC(self):
        """Internal function. Returns MAC address."""
        MAC = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
        return ':'.join([MAC[i:i+2] for i in range(0, 11, 2)])

    def _user_connection_error_wrapper(function):
        """Internal decorator. Raise LoginConnectionError if can't connect."""
        @functools.wraps(function)
        def wrapped_function(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except requests.exceptions.RequestException as error:
                raise LoginConnectionError(str(error)) from error
        return wrapped_function

    @_user_connection_error_wrapper
    @functools.wraps(requests.Session.request)
    def request(self, *args, **kwargs):
        return Page(self, self.session.request(*args, **kwargs))

    @_user_connection_error_wrapper
    @functools.wraps(requests.Session.get)
    def get(self, *args, **kwargs):
        return Page(self, self.session.get(*args, **kwargs))

    @_user_connection_error_wrapper
    @functools.wraps(requests.Session.post)
    def post(self, *args, **kwargs):
        return Page(self, self.session.post(*args, **kwargs))

    def auth(self):
        """Logins to YKPS Wi-Fi.
        Derived from: https://github.com/yu-george/AutoAuth-YKPS/
        """
        self._login_web_auth()
        self._login_blue_auth()

    def _login_web_auth(self):
        """Internal function."""
        url = 'https://auth.ykpaoschool.cn/portalAuthAction.do'
        payload = {
            'wlanuserip': self.IP,
            'mac': self.MAC,
            'wlanacname': 'hh1u6p',
            'wlanacIp': '192.168.186.2',
            'userid': self.username,
            'passwd': self.password,
        }
        with warnings.catch_warnings(): # Catch warning
            warnings.simplefilter('ignore', category=InsecureRequestWarning)
            return self.post(url, data=payload, verify=False)

    def _login_blue_auth(self):
        """Internal function."""
        redirect = self.get('http://www.apple.com/cn/', allow_redirects=True)
        query = parse_qs(redirect.url().query)
        oldURL = query.get('oldURL')
        authServ = query.get('authServ')
        if oldURL is None or authServ is None:
            return redirect
        else:
            payload = {
                'txtUserName': self.username,
                'txtPasswd': self.password,
                'oldURL': oldURL,
                'authServ': authServ
            }
            with warnings.catch_warnings(): # Catch warning
                warnings.simplefilter(
                    'ignore', category=InsecureRequestWarning)
                return self.post('http://192.168.1.1:8181/',
                    data=payload, verify=False)

    def ps_login(self):
        """Returns login to Powerschool Page."""
        ps_login = self.get(
            'https://powerschool.ykpaoschool.cn/public/home.html')
        if ps_login.url().path == '/guardian/home.html':
            # If already logged in
            return ps_login
        payload = ps_login.payload()
        payload_updates = {
            'dbpw': hmac.new(payload['contextData'].encode('ascii'),
                self.password.lower().encode('ascii'),
                hashlib.md5).hexdigest(),
            'account': self.username,
            'pw': hmac.new(payload['contextData'].encode('ascii'),
                base64.b64encode(hashlib.md5(self.password.encode('ascii')
                    ).digest()).replace(b'=', b''), hashlib.md5).hexdigest(),
            'ldappassword': self.password if 'ldappassword' in payload else ''
        }
        return ps_login.submit(updates=payload_updates, id='LoginForm')

    def ms_login(self, redirect_to_ms=None):
        """Returns login to Microsoft Page.

        redirect_to_ms: requests.models.Response or str, the page that a login
                        page redirects to for Microsoft Office365 login,
                        defaults to GET 'https://login.microsoftonline.com/'.
        """
        if redirect_to_ms is None:
            # Default if page not specified
            redirect_to_ms = self.get('https://login.microsoftonline.com/')
        if len(redirect_to_ms.text().splitlines()) == 1:
            # If already logged in
            return redirect_to_ms.submit(redirect_to_ms)
        ms_login_CDATA = redirect_to_ms.CDATA()
        ms_get_credential_type_payload = json.dumps({ # have to use json
            'username': self.username + '@ykpaoschool.cn',
            'isOtherIdpSupported': True,
            'checkPhones': False,
            'isRemoteNGCSupported': False,
            'isCookieBannerShown': False,
            'isFidoSupported': False,
            'originalRequest': ms_login_CDATA['sCtx'],
            'country': ms_login_CDATA['country'],
            'flowToken': ms_login_CDATA['sFT'],
        })
        ms_get_credential_type = self.post(
            'https://login.microsoftonline.com'
            '/common/GetCredentialType?mkt=en-US',
            data=ms_get_credential_type_payload
        ).json()
        adfs_login = self.get(
            ms_get_credential_type['Credentials']['FederationRedirectUrl'])
        adfs_login_payload = adfs_login.payload(
            updates={
                'ctl00$ContentPlaceHolder1$UsernameTextBox': self.username,
                'ctl00$ContentPlaceHolder1$PasswordTextBox': self.password,
        })
        adfs_login_form_url = adfs_login.form().get('action')
        if urlparse(adfs_login_form_url).netloc == '':
            # If intermediate page exists
            adfs_intermediate_url = (
                'https://adfs.ykpaoschool.cn' + adfs_login_form_url)
            adfs_intermediate = self.post(adfs_intermediate_url,
                data=adfs_login_payload)
            adfs_intermediate_payload = adfs_intermediate.payload()
            back_to_ms_url = adfs_intermediate.form().get('action')
            if urlparse(back_to_ms_url).netloc == '':
                # If stays in adfs, username or password is incorrect
                raise WrongUsernameOrPassword(
                    'Incorrect username or password.')
        else:
            # If intermediate page does not exist
            back_to_ms_url = adfs_login_form_url
            adfs_intermediate_payload = adfs_login_payload
        ms_confirm = self.post(back_to_ms_url, data=adfs_intermediate_payload)
        if ms_confirm.url().netloc != 'login.microsoftonline.com':
            # If ms_confirm is skipped, sometimes happens
            return ms_confirm
        ms_confirm_CDATA = ms_confirm.CDATA()
        ms_confirm_payload = {
            'LoginOptions': 0,
            'ctx': ms_confirm_CDATA['sCtx'],
            'hpgrequestid': ms_confirm_CDATA['sessionId'],
            'flowToken': ms_confirm_CDATA['sFT'],
            'canary': ms_confirm_CDATA['canary'],
            'i2': None,
            'i17': None,
            'i18': None,
            'i19': 66306,
        }
        ms_out_url = 'https://login.microsoftonline.com/kmsi'
        ms_out = self.post(ms_out_url, data=ms_confirm_payload)
        if ms_out.url().geturl() in ms_out_url:
            # If encounters 'Working...' page
            return ms_out.submit()
        else:
            return ms_out

    def psl_login(self):
        """Returns login to Powerschool Learning Page."""
        psl_url = 'ykpaoschool.learning.powerschool.com'
        psl_login = self.get(
            'https://' + psl_url + '/do/oauth2/office365_login')
        if psl_login.url().netloc == psl_url:
            # If already logged in
            return psl_login
        return self.ms_login(redirect_to_ms=psl_login)
