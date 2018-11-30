"""Class 'User' that stores its user info and functions."""

__all__ = ['User']

import re
import json
from os import popen
from os.path import exists, expanduser
from hmac import new
from hashlib import md5
from base64 import b64encode, b64decode
from getpass import getpass
from socket import gethostbyname, gethostname, getfqdn
from uuid import UUID, getnode
from urllib.parse import unquote, urlparse
from urllib3.exceptions import InsecureRequestWarning
from warnings import catch_warnings, filterwarnings
from functools import wraps

import requests

from .page import Page
from .exceptions import (LoginConnectionError, WrongUsernameOrPassword,
    GetUsernamePasswordError, GetIPError)


class User:

    """Class 'User' that stores its user info and functions."""

    def __init__(self, username=None, password=None, load=True,
        prompt=False, session_args=(), session_kwargs={}):
        """Initialize a User.

        username_password: (username: str, password: str), defaults to
                           creds.load()
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
                    except GetUsernamePasswordError as error:
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
        usr_dat = expanduser(
        '~/Library/Application Support/AutoAuth/usr.dat')
        if not exists(usr_dat):
            raise GetUsernamePasswordError("'usr.dat' not found.")
        try:
            with open(usr_dat) as file:
                username = file.readline().strip()
                password = b64decode(
                    file.readline().strip().encode()).decode()
        except (OSError, IOError) as error:
            raise GetUsernamePasswordError(
                "Error when opening 'usr.dat'") from error
        if not username or not password:
            raise GetUsernamePasswordError(
                "'usr.dat' contains invalid username or password.") 
        return username, password

    def _prompt(self):
        """Internal function."""
        username = input('Enter username (e.g. s12345): ').strip()
        password = getpass('Password for %s: ' % username).strip()
        return username, password

    def _get_IP(self):
        """Returns private IP address."""
        try:
            IP = gethostbyname(gethostname())
        except Exception:
            try:
                IP = gethostbyname(getfqdn())
            except Exception:
                IP = popen("ifconfig | grep 'inet ' | grep -v '127.0' | xargs"
                    " | awk -F '[ :]' '{print $2}'").readline().strip()
                if not IP:
                    raise GetIPError("Can't retrieve IP address.")
        return IP

    def _get_MAC(self):
        """Returns MAC address."""
        MAC = ':'.join([UUID(int=getnode()).hex[-12:].upper()[i:i+2]
            for i in range(0, 11, 2)])
        return MAC

    def _user_connection_error_wrapper(function):
        """Internal decorator."""
        @wraps(function)
        def wrapped_function(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except requests.exceptions.ConnectionError as error:
                raise LoginConnectionError(str(error)) from error
        return wrapped_function

    @_user_connection_error_wrapper
    def request(self, *args, **kwargs):
        return Page(self, self.session.request(*args, **kwargs))

    @_user_connection_error_wrapper
    def get(self, *args, **kwargs):
        return Page(self, self.session.get(*args, **kwargs))

    @_user_connection_error_wrapper
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
        form_data = {
            'wlanuserip': self.IP,
            'mac': self.MAC,
            'wlanacname': 'hh1u6p',
            'wlanacIp': '192.168.186.2',
            'userid': self.username,
            'passwd': self.password,
        }
        with catch_warnings(): # Catch warning
            filterwarnings('ignore', category=InsecureRequestWarning)
            return self.post(url, data=form_data, verify=False)

    def _login_blue_auth(self):
        """Internal function."""
        web = self.get('http://www.apple.com/cn/', allow_redirects=True)
        oldURL_and_authServ = re.compile(
            r'oldURL=([^&]+)&authServ=(.+)').findall(unquote(web.url()))
        if oldURL_and_authServ:
            oldURL, authServ = oldURL_and_authServ[0]
        else:
            return None
        form_data = {
            'txtUserName': self.username,
            'txtPasswd': self.password,
            'oldURL': oldURL,
            'authServ': authServ
        }
        with catch_warnings(): # Catch warning
            filterwarnings('ignore', category=InsecureRequestWarning)
            return self.post('http://192.168.1.1:8181/',
                data=form_data, verify=False)

    def ps_login(self):
        """Returns login to Powerschool response."""
        # Request login page to Powerschool
        ps_login = self.get(
            'https://powerschool.ykpaoschool.cn/public/home.html')
        # If already logged in
        if ps_login.url().path == '/guardian/home.html':
            return ps_login
        # Parse login page and send login form
        payload = ps_login.payload()
        payload_updates = {
            'dbpw': new(payload['contextData'].encode('ascii'),
                self.password.lower().encode('ascii'), md5).hexdigest(),
            'account': self.username,
            'pw': new(payload['contextData'].encode('ascii'),
                b64encode(md5(self.password.encode('ascii')).digest()
                    ).replace(b'=', b''), md5).hexdigest(),
            'ldappassword': self.password if 'ldappassword' in payload else ''
        }
        return ps_login.submit(updates=payload_updates, id='LoginForm')

    def ms_login(self, redirect_to_ms=None):
        """Returns login to Microsoft response.

        redirect_to_ms: requests.Response or str, the page that a login page
                        redirects to for Microsoft Office365 login, defaults
                        to GET 'https://login.microsoftonline.com/'
        """
        # Default if page not specified
        if redirect_to_ms is None:
            redirect_to_ms = self.get('https://login.microsoftonline.com/')
        # If already logged in to Microsoft Office365
        if len(redirect_to_ms.text().splitlines()) == 1:
            return redirect_to_ms.submit(redirect_to_ms)
        # Get credential type of Microsoft login
        ms_login_CDATA = redirect_to_ms.CDATA()
        ms_get_credential_type_payload = {
            'username': self.username + '@ykpaoschool.cn',
            'isOtherIdpSupported': True,
            'checkPhones': False,
            'isRemoteNGCSupported': False,
            'isCookieBannerShown': False,
            'isFidoSupported': False,
            'originalRequest': ms_login_CDATA['sCtx'],
            'country': 'CN',
            'flowToken': ms_login_CDATA['sFT'],
        }
        ms_get_credential_type = self.post(
            'https://login.microsoftonline.com'
            '/common/GetCredentialType?mkt=en-US',
            data=json.dumps(ms_get_credential_type_payload)
        ).json()
        # Redirect to organization page (https://adfs.ykpaoschool.cn)
        adfs_login = self.get(
            ms_get_credential_type['Credentials']['FederationRedirectUrl'])
        # Load form to intermediate page or to Microsoft
        adfs_login_payload = adfs_login.payload(
            updates={
                'ctl00$ContentPlaceHolder1$UsernameTextBox': self.username,
                'ctl00$ContentPlaceHolder1$PasswordTextBox': self.password,
        })
        adfs_login_form_url = adfs_login.form().get('action')
        # If intermediate page exists
        if urlparse(adfs_login_form_url).netloc == '':
            # Post to intermediate page
            adfs_intermediate_url = (
                'https://adfs.ykpaoschool.cn' + adfs_login_form_url)
            adfs_intermediate = self.post(adfs_intermediate_url,
                data=adfs_login_payload)
            # Load payload back to Microsoft login page
            adfs_intermediate_payload = adfs_intermediate.payload()
            back_to_ms_url = adfs_intermediate.form().get('action')
            # If stays in adfs, username or password is incorrect
            if urlparse(back_to_ms_url).netloc == '':
                raise WrongUsernameOrPassword(
                    'Incorrect username or password.')
        # If intermediate page does not exist
        else:
            back_to_ms_url = adfs_login_form_url
            adfs_intermediate_payload = adfs_login_payload
        # Send to Microsoft "Stay logged in?" page, and say no
        ms_confirm = self.post(back_to_ms_url, data=adfs_intermediate_payload)
        # If this page is skipped, sometimes happens
        if ms_confirm.url().netloc != 'login.microsoftonline.com':
            return ms_confirm
        ms_confirm_CDATA = ms_confirm.CDATA()
        # Tell Microsoft login not to stay logged in
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
        if ms_out.url().geturl() == ms_out_url:
            # If encounters 'Working...' page
            return ms_out.submit()
        else:
            return ms_out

    def psl_login(self):
        """Returns login to Powerschool Learning response."""
        # Login by Office 365 on Powerschool Learning
        psl_url = 'ykpaoschool.learning.powerschool.com'
        psl_login = self.get(
            'https://' + psl_url + '/do/oauth2/office365_login')
        # Check if already logged in
        if psl_login.url().netloc == psl_url:
            return psl_login
        # Login through Microsoft
        return self.ms_login(redirect_to_ms=psl_login)
