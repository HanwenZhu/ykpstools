"""Class 'Page' is a wrapper around requests.Response with convenient
functions.
"""

__all__ = ['Page', 'LoginPageBase', 'AuthPage', 'PowerschoolPage',
    'MicrosoftPage', 'PowerschoolLearningPage']
__author__ = 'Thomas Zhu'

import abc
import base64
import hashlib
import hmac
import json
import re
import socket
import subprocess
import sys
from urllib.parse import urlparse, urljoin
from urllib3.exceptions import InsecureRequestWarning
import warnings

import requests
from bs4 import BeautifulSoup

from ykpstools.exceptions import WrongUsernameOrPassword, GetIPError


class Page(abc.ABC):

    """Class 'Page' is a wrapper around requests.Response with convenient
    functions.
    """

    def __init__(self, user, response):
        """Initialize a Page.
        
        user: a ykpstools.user.User instance, the User this page belongs to,
        response: a requests.Response instance or
                          a ykpstools.page.Page instance.
        """
        self.user = user
        if isinstance(response, requests.Response):
            self.response = response
        elif isinstance(response, Page):
            self.response = response.response

    def url(self, *args, **kwargs):
        """Get current URL.
        
        *args: arguments for urllib.parse.urlparse,
        *kwargs: keyword arguments for urllib.parse.urlparse."""
        return urlparse(self.response.url, *args, **kwargs)

    def text(self, encoding=None):
        """Returns response text.
        
        encoding=None: encoding charset for HTTP, defaults to obtain from
                       headers.
        """
        if encoding is not None:
            self.response.encoding = encoding
        return self.response.text

    def soup(self, features='lxml', *args, **kwargs):
        """Returns bs4.BeautifulSoup of this page.
        
        features='lxml': 'features' keyword argument for BeautifulSoup,
        *args: arguments for BeautifulSoup,
        **kwargs: keyword arguments for BeautifulSoup.
        """
        return BeautifulSoup(self.text(), features=features, *args, **kwargs)

    def CDATA(self):
        """Gets the CDATA of this page."""
        return json.loads(re.findall(
            r'//<!\[CDATA\[\n\$Config=(.*?);\n//\]\]>', self.text())[0])

    def form(self, *find_args, **find_kwargs):
        """Gets HTML element form as bs4.element.Tag of this page.
        
        *find_args: arguments for BeautifulSoup.find('form'),
        **find_kwargs: keyword arguments for BeautifulSoup.find('form').
        """
        return self.soup().find('form', *find_args, **find_kwargs)

    def payload(self, updates={}, *find_args, **find_kwargs):
        """Load completed form of this page.
        
        updates: updates to payload,
        *find_args: arguments for BeautifulSoup.find('form'),
        **find_kwargs: keyword arguments for BeautifulSoup.find('form').
        """
        form = self.form(*find_args, **find_kwargs)
        if form is None:
            return updates
        else:
            payload = {
                i.get('name'): i.get('value')
                for i in form.find_all('input')
                if i.get('name') is not None}
            payload.update(updates)
            return payload

    def submit(self, updates={}, find_args=(), find_kwargs={},
        *args, **kwargs):
        """Submit form from page.
        
        updates: updates to payload,
        find_args: arguments for BeautifulSoup.find('form'),
        find_kwargs: keyword arguments for BeautifulSoup.find('form'),
        *args: arguments for User.request,
        **kwargs: keyword arguments for User.request.
        """
        form = self.form(*find_args, **find_kwargs)
        if form is None:
            return self
        else:
            method = form.get('method')
            action = urljoin(self.url().geturl(), form.get('action'))
            payload = self.payload(updates, *find_args, **find_kwargs)
            return self.user.request(method, action,
                data=payload, *args, **kwargs)

    def json(self, *args, **kwargs):
        """Returns response in json format.
        
        *args: arguments for requests.Response.json,
        *kwargs: keyword arguments for requests.Response.json.
        """
        return self.response.json(*args, **kwargs)


class LoginPageBase(Page):

    """Basic login Page class for pages that involve specific logins."""

    def __init__(self, user, *args, **kwargs):
        """Log in to a url in self.login to initialize.
        
        user: a ykpstools.user.User instance, the User this page belongs to,
        *args: arguments for self.login,
        **kwargs: keyword arguments for self.login.
        """
        self.user = user
        page = self.login(*args, **kwargs)
        super().__init__(self.user, page)

    @abc.abstractmethod
    def login(self, *args, **kwargs):
        """For login during initialization.
        Should override in its subclasses.
        """
        page = None # Should override in its subclasses.
        return page


class AuthPage(LoginPageBase):

    """Class 'AuthPage' inherits and adds on specific initialization and
    attributes for YKPS WiFi Authorization to 'ykpstools.page.Page'.
    """

    def __init__(self, user, *args, **kwargs):
        """Log in to WiFi to initialize.
        
        user: a ykpstools.user.User instance, the User this page belongs to.
        *args: arguments for POST to http://auth.ykpaoschool.cn
        *kwargs: keyword arguments for POST to http://auth.ykpaoschool.cn
        """
        super().__init__(user, *args, **kwargs)

    def login(self, *args, **kwargs):
        """For login to WiFi during initialization."""
        self.mac_connect_to_wifi()
        ext_portal = self.user.get('http://1.1.1.1:8000/ext_portal.magi',
            *args, **kwargs)
        # html is like <script>location.replace("url")</script>, hence
        url = re.findall(
            r'''location\.replace\(['"](.*)['"]\);''', ext_portal.text())[0]
        if url == 'http://1.1.1.1:8000/logout.htm':
            return ext_portal
        with warnings.catch_warnings(): # catch InsecureRequestWarning
            warnings.simplefilter('ignore', category=InsecureRequestWarning)
            portal = self.user.get(url, verify=False)
            credentials = {
                'userid': self.user.username, 'passwd': self.user.password}
            credentials.update(kwargs.get('updates', {}))
            submit_auth = portal.submit( # no redirects to make process faster
                updates=credentials, verify=False, allow_redirects=False)
            if submit_auth.response.status_code == 200: # should not happen
                # html is like <script>alert('error')</script>, hence
                raise WrongUsernameOrPassword('From server: ' + re.findall(
                    r'''alert\(['"](.*)['"]\);''', submit_auth.text())[0])
            else:
                return submit_auth

    def logout(self, *args, **kwargs):
        """Logouts from YKPS Wi-Fi, with args and kwargs for self.user.get."""
        return self.user.get('http://1.1.1.1/userout.magi', *args, **kwargs)

    @property
    def unix_interfaces(self):
        if sys.platform == 'darwin':
            networksetup = subprocess.check_output(
                'networksetup -listallhardwareports |'
                'grep "Device: "',
                shell=True, stderr=subprocess.DEVNULL).decode()
            return [n.strip().split()[-1]
                for n in networksetup.splitlines()]
        elif sys.platform.startswith('linux'):
            return ['eth0', 'wlan0', 'wifi0', 'eth1',
                'eth2', 'wlan1', 'ath0', 'ath1', 'ppp0', 'en0', 'en1']
        else:
            return [NotImplemented]

    def mac_connect_to_wifi(self):
        if sys.platform == 'darwin':
            interface = self.unix_interfaces[0]
            is_network_on = subprocess.check_output(
                'networksetup -getairportpower {}'.format(interface),
                shell=True, stderr=subprocess.DEVNULL
            ).decode().strip().split()[-1] == 'On'
            if not is_network_on:
                subprocess.check_output(
                    'networksetup -setairportpower {} on'.format(interface),
                    shell=True, stderr=subprocess.DEVNULL)
            is_correct_wifi = subprocess.check_output(
                    'networksetup -getairportnetwork {}'.format(interface),
                    shell=True, stderr=subprocess.DEVNULL
                ).decode().strip().split()[-1] in {
                'GUEST', 'STUWIRELESS', 'SJWIRELESS'}
            if not is_correct_wifi:
                subprocess.check_output(
                    'networksetup -setairportnetwork {} {} {}'.format(
                        interface, 'STUWIRELESS', ''),
                    shell=True, stderr=subprocess.DEVNULL)
            while True:
                try:
                    subprocess.check_output(
                        'ping auth.ykpaoschool.cn' # ping blocks until wifi ready
                        ' -c 1 -W 1 -i 0.1', # waits for 0.1 second each loop
                        shell=True, stderr=subprocess.DEVNULL)
                except subprocess.CalledProcessError:
                    continue
                else:
                    break

    @property
    def IP(self):
        """Returns IP address in LAN."""
        def _is_valid_IP(IP):
            """Internal function. Check if IP is internal IPv4 address."""
            if (IP and isinstance(IP, str) and not IP.startswith('127.')
                and re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', IP)):
                return True
            else:
                return False
        try:
            IP = socket.gethostbyname(socket.gethostname())
            assert _is_valid_IP(IP)
        except (socket.error, AssertionError):
            try:
                IP = socket.gethostbyname(socket.getfqdn())
                assert _is_valid_IP(IP)
            except (socket.error, AssertionError):
                if sys.platform in {'win32', 'win16', 'dos', 'cygwin'}:
                    try:
                        ipconfig = subprocess.check_output('ipconfig /all',
                            shell=True, stderr=subprocess.DEVNULL).decode()
                    except subprocess.CalledProcessError as error:
                        raise GetIPError(
                            "Can't retrieve IP address.") from error
                    else:
                        for ipconfig_line in ipconfig.splitlines():
                            line = ipconfig_line.strip()
                            if re.search(r'[\s^]IP(?:v4)?[\s\:$]', line):
                                # 'IP' or 'IPv4'
                                IP = line.split()[-1]
                                if _is_valid_IP(IP):
                                    break
                        else:
                            raise GetIPError("Can't retrieve IP address.")
                elif (sys.platform == 'darwin'
                    or sys.platform.startswith('linux')):
                    interfaces = self.unix_interfaces
                    for interface in interfaces:
                        try:
                            ifconfig = subprocess.check_output(
                                'ifconfig {} | grep "inet "'.format(interface),
                                shell=True, stderr=subprocess.DEVNULL).decode()
                            IP = ifconfig.splitlines()[0].strip().split()[1]
                            assert _is_valid_IP(IP)
                        except (subprocess.CalledProcessError,
                            AssertionError, IndexError):
                            continue
                        else:
                            break
                    else:
                        raise GetIPError("Can't retrieve IP address. "
                            'Maybe your network is disabled or disconnected?')
                else:
                    raise GetIPError('Not implemented OS: ' + sys.platform)
        if not _is_valid_IP(IP):
            raise GetIPError("Can't retrieve IP address.")
        else:
            return IP

    @property
    def MAC(self):
        """Returns MAC address."""
        MAC = uuid.UUID(int=uuid.getnode()).hex[-12:].upper()
        return ':'.join([MAC[i:i+2] for i in range(0, 11, 2)])


class PowerschoolPage(LoginPageBase):

    """Class 'PowerschoolPage' inherits and adds on specific initialization and
    attributes for Powerschool to 'ykpstools.page.Page'.
    """

    def __init__(self, user):
        """Log in to Powerschool to initialize.
        
        user: a ykpstools.user.User instance, the User this page belongs to.
        """
        super().__init__(user)

    def login(self):
        """For login to Powerschool during initialization."""
        ps_login = self.user.get(
            'https://powerschool.ykpaoschool.cn/public/home.html')
        if ps_login.url().path == '/guardian/home.html': # If already logged in
            return ps_login
        payload = ps_login.payload()
        payload_updates = {
            'dbpw': hmac.new(payload['contextData'].encode('ascii'),
                self.user.password.lower().encode('ascii'),
                hashlib.md5).hexdigest(),
            'account': self.user.username,
            'pw': hmac.new(payload['contextData'].encode('ascii'),
                base64.b64encode(hashlib.md5(self.user.password.encode('ascii')
                    ).digest()).replace(b'=', b''), hashlib.md5).hexdigest(),
            'ldappassword': (self.user.password if 'ldappassword' in payload
                else '')
        }
        submit_login = ps_login.submit(updates=payload_updates)
        if submit_login.soup().title.string == 'Student and Parent Sign In':
            raise WrongUsernameOrPassword
        return submit_login


class MicrosoftPage(LoginPageBase):

    """Class 'MicrosoftPage' inherits and adds on specific initialization and
    attributes for Microsoft to 'ykpstools.page.Page'.
    """

    def __init__(self, user, redirect_to_ms=None):
        """Log in to Microsoft to initialize.
        
        user: a ykpstools.user.User instance, the User this page belongs to,
        redirect_to_ms: requests.models.Response or str, the page that a login
                        page redirects to for Microsoft Office365 login,
                        defaults to
                        user.get('https://login.microsoftonline.com/').
        """
        super().__init__(user, redirect_to_ms)

    def login(self, redirect_to_ms=None):
        """For login to Microsoft during initialization.
        
        redirect_to_ms: requests.models.Response or str, the page that a login
                        page redirects to for Microsoft Office365 login,
                        defaults to
                        self.user.get('https://login.microsoftonline.com/').
        """
        if redirect_to_ms is None: # Default if page not specified
            redirect_to_ms = self.user.get('https://login.microsoftonline.com')
        if len(redirect_to_ms.text().splitlines()) == 1:
            # If already logged in
            return redirect_to_ms.submit()
        ms_login_CDATA = redirect_to_ms.CDATA()
        ms_get_credential_type_payload = json.dumps({ # have to use json
            'username': self.user.username + '@ykpaoschool.cn',
            'isOtherIdpSupported': True,
            'checkPhones': False,
            'isRemoteNGCSupported': False,
            'isCookieBannerShown': False,
            'isFidoSupported': False,
            'originalRequest': ms_login_CDATA['sCtx'],
            'country': ms_login_CDATA['country'],
            'flowToken': ms_login_CDATA['sFT'],
        })
        ms_get_credential_type = self.user.post(
            'https://login.microsoftonline.com'
            '/common/GetCredentialType?mkt=en-US',
            data=ms_get_credential_type_payload
        ).json()
        adfs_login = self.user.get(
            ms_get_credential_type['Credentials']['FederationRedirectUrl'])
        adfs_login_payload = adfs_login.payload(updates={
            'ctl00$ContentPlaceHolder1$UsernameTextBox': self.user.username,
            'ctl00$ContentPlaceHolder1$PasswordTextBox': self.user.password,
        })
        adfs_login_form_url = adfs_login.form().get('action')
        if urlparse(adfs_login_form_url).netloc == '':
            # If intermediate page exists
            adfs_intermediate_url = urljoin(
                'https://adfs.ykpaoschool.cn', adfs_login_form_url)
            adfs_intermediate = self.user.post(adfs_intermediate_url,
                data=adfs_login_payload)
            adfs_intermediate_payload = adfs_intermediate.payload()
            back_to_ms_url = adfs_intermediate.form().get('action')
            if urlparse(back_to_ms_url).netloc == '':
                # If stays in adfs, username or password is incorrect
                raise WrongUsernameOrPassword
        else:
            # If intermediate page does not exist
            back_to_ms_url = adfs_login_form_url
            adfs_intermediate_payload = adfs_login_payload
        ms_confirm = self.user.post(back_to_ms_url,
            data=adfs_intermediate_payload)
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
        ms_out = self.user.post(ms_out_url, data=ms_confirm_payload)
        if ms_out_url in ms_out.url().geturl():
            # If encounters 'Working...' page
            return ms_out.submit()
        else:
            return ms_out


class PowerschoolLearningPage(LoginPageBase):

    """Class 'PowerschoolLearningPage' inherits and adds on specific
    initialization and attributes for Powerschool Learning to
    'ykpstools.page.Page'.
    """

    def __init__(self, user):
        """Log in to Powerschool Learning to initialize.
        
        user: a ykpstools.user.User instance, the User this page belongs to.
        """
        super().__init__(user)

    def login(self):
        """For login to Powerschool Learning during initialization."""
        psl_login = self.user.get(urljoin(
            'https://ykpaoschool.learning.powerschool.com',
            '/do/oauth2/office365_login'))
        if psl_login.url().netloc == 'ykpaoschool.learning.powerschool.com':
            # If already logged in
            return psl_login
        else:
            return self.user.microsoft(psl_login)

    @property
    def classes(self):
        """The 'classes' property parses and returns the classes from the home
        page.
        """
        return {
            div.find('a').string:
            urljoin(self.url().geturl(), div.find('a').get('href'))
            for div in self.soup().find_all('div', class_='eclass_filter')}
