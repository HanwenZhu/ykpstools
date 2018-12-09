"""Class 'Page' is a wrapper around requests.Response with convenient
functions.
"""

__all__ = ['Page', 'PowerschoolPage', 'MicrosoftPage',
    'PowerschoolLearningPage']
__author__ = 'Thomas Zhu'

import base64
import functools
import hashlib
import hmac
import json
import re
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup


class Page:

    """Class 'Page' is a wrapper around requests.Response with convenient
    functions.
    """

    def __init__(self, user, response):
        """Initialize a Page.
        
        user: a ykpstools.user.User instance, the User this page belongs to,
        response: a requests.Response instance.
        """
        self.response = response
        self.response.encoding = 'utf-8'
        self.user = user

    def url(self, *args, **kwargs):
        """Get current URL.
        
        *args: arguments for urllib.parse.urlparse,
        *kwargs: keyword arguments for urllib.parse.urlparse."""
        return urlparse(self.response.url, *args, **kwargs)

    def text(self):
        """Returns response text."""
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
        
        *find_args: arguments for BeautifulSoup.find('form'),
        updates: updates to payload,
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


class PowerschoolPage(Page):

    """Class 'PowerschoolPage' inherits and adds on specific initialization and
    attributes for Powerschool to 'ykpstools.page.Page'.
    """

    def __init__(self, user):
        """Log in to Powerschool to initialize.
        
        user: a ykpstools.user.User instance, the User this page belongs to.
        """
        ps_login = user.get(
            'https://powerschool.ykpaoschool.cn/public/home.html')
        if ps_login.url().path == '/guardian/home.html': # If already logged in
            response = ps_login.response
        else:
            payload = ps_login.payload()
            payload_updates = {
                'dbpw': hmac.new(payload['contextData'].encode('ascii'),
                    user.password.lower().encode('ascii'),
                    hashlib.md5).hexdigest(),
                'account': user.username,
                'pw': hmac.new(payload['contextData'].encode('ascii'),
                    base64.b64encode(hashlib.md5(user.password.encode('ascii')
                        ).digest()).replace(b'=', b''),
                    hashlib.md5).hexdigest(),
                'ldappassword': (user.password if 'ldappassword' in payload
                    else '')
            }
            response = ps_login.submit(updates=payload_updates).response
        super().__init__(user, response)


class MicrosoftPage(Page):

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
        if redirect_to_ms is None: # Default if page not specified
            redirect_to_ms = user.get('https://login.microsoftonline.com/')
        if len(redirect_to_ms.text().splitlines()) == 1:
            # If already logged in
            response = redirect_to_ms.submit().response
        else:
            ms_login_CDATA = redirect_to_ms.CDATA()
            ms_get_credential_type_payload = json.dumps({ # have to use json
                'username': user.username + '@ykpaoschool.cn',
                'isOtherIdpSupported': True,
                'checkPhones': False,
                'isRemoteNGCSupported': False,
                'isCookieBannerShown': False,
                'isFidoSupported': False,
                'originalRequest': ms_login_CDATA['sCtx'],
                'country': ms_login_CDATA['country'],
                'flowToken': ms_login_CDATA['sFT'],
            })
            ms_get_credential_type = user.post(
                'https://login.microsoftonline.com'
                '/common/GetCredentialType?mkt=en-US',
                data=ms_get_credential_type_payload
            ).json()
            adfs_login = user.get(
                ms_get_credential_type['Credentials']['FederationRedirectUrl'])
            adfs_login_payload = adfs_login.payload(updates={
                    'ctl00$ContentPlaceHolder1$UsernameTextBox': user.username,
                    'ctl00$ContentPlaceHolder1$PasswordTextBox': user.password,
            })
            adfs_login_form_url = adfs_login.form().get('action')
            if urlparse(adfs_login_form_url).netloc == '':
                # If intermediate page exists
                adfs_intermediate_url = (
                    'https://adfs.ykpaoschool.cn' + adfs_login_form_url)
                adfs_intermediate = user.post(adfs_intermediate_url,
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
            ms_confirm = user.post(back_to_ms_url,
                data=adfs_intermediate_payload)
            if ms_confirm.url().netloc != 'login.microsoftonline.com':
                # If ms_confirm is skipped, sometimes happens
                response = ms_confirm.response
            else:
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
                ms_out = user.post(ms_out_url, data=ms_confirm_payload)
                if ms_out.url().geturl() in ms_out_url:
                    # If encounters 'Working...' page
                    response = ms_out.submit().response
                else:
                    response = ms_out.response
        super().__init__(user, response)


class PowerschoolLearningPage(Page):

    """Class 'PowerschoolLearningPage' inherits and adds on specific
    initialization and attributes for Powerschool Learning to
    'ykpstools.page.Page'.
    """

    def __init__(self, user):
        """Log in to Powerschool Learning to initialize.
        
        user: a ykpstools.user.User instance, the User this page belongs to.
        """
        psl_url = 'ykpaoschool.learning.powerschool.com'
        psl_login = user.get(
            'https://' + psl_url + '/do/oauth2/office365_login')
        if psl_login.url().netloc == psl_url: # If already logged in
            response = psl_login.response
        else:
            response = user.microsoft(psl_login).response
        super().__init__(user, response)
