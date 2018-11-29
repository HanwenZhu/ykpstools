"""Login tools for various websites."""

import json
from urllib.parse import urlparse

import requests

from exceptions import (
    WrongUsernameOrPassword, GetUsernamePasswordError)
from creds import load
from webutils import (
    set_up_session, load_text, load_soup, load_CDATA, load_form, load_payload,
    submit_form)


def ps_login(username, password, session=requests.Session()):
    """Login to Powerschool.
    Returns a requests.Response instance.

    username: str,
    password: str,

    session: requests.Session, defaults to requests.Session().
    """
    # Request login page to Powerschool
    ps_login = session.get(
        'https://powerschool.ykpaoschool.cn/public/home.html')

    # Parse login page and send login form
    return submit_form(ps_login, session=session,
        updates={'account': username, 'pw': password}, id='LoginForm')


def ms_login(username, password, session=requests.Session(),
    redirect_to_ms=None, load_page_after_login=True):
    """Login to Microsoft Office365.
    Returns a requests.Response instance.

    username: str,
    password: str,

    session: requests.Session, defaults to requests.Session().
    redirect_to_ms: requests.Response or str, the page that a login page
                    redirects to for Microsoft Office365 login, defaults to
                    GET 'https://login.microsoftonline.com/'
    load_page_after_login: load page after login, defaults to True
    """
    # Default if page not specified
    if redirect_to_ms is None:
        redirect_to_ms = session.get('https://login.microsoftonline.com/')
    else:
        redirect_to_ms = redirect_to_ms

    # If already logged in to Microsoft Office365
    if len(load_text(redirect_to_ms).splitlines()) == 1:
        return submit_form(redirect_to_ms, session=session)

    # Get credential type of Microsoft login
    ms_login_CDATA = load_CDATA(redirect_to_ms)
    ms_get_credential_type_payload = {
        'username': username + '@ykpaoschool.cn',
        'isOtherIdpSupported': True,
        'checkPhones': False,
        'isRemoteNGCSupported': False,
        'isCookieBannerShown': False,
        'isFidoSupported': False,
        'originalRequest': ms_login_CDATA['sCtx'],
        'country': 'CN',
        'flowToken': ms_login_CDATA['sFT'],
    }
    ms_get_credential_type = session.post(
        'https://login.microsoftonline.com'
        '/common/GetCredentialType?mkt=en-US',
        data=json.dumps(ms_get_credential_type_payload)
    ).json()

    # Redirect to organization page (https://adfs.ykpaoschool.cn)
    adfs_login = session.get(
        ms_get_credential_type['Credentials']['FederationRedirectUrl'])

    # Load form to intermediate page or to Microsoft
    adfs_login_payload = load_payload(adfs_login, updates={
        'ctl00$ContentPlaceHolder1$UsernameTextBox': username,
        'ctl00$ContentPlaceHolder1$PasswordTextBox': password,
    })
    adfs_login_form_url = load_form(adfs_login).get('action')

    # If intermediate page exists
    if adfs_login_form_url.startswith('/'):
        # Post to intermediate page
        adfs_intermediate_url = (
            'https://adfs.ykpaoschool.cn' + adfs_login_form_url)
        adfs_intermediate = session.post(adfs_intermediate_url,
            data=adfs_login_payload)
        # Load payload back to Microsoft login page
        adfs_intermediate_payload = load_payload(adfs_intermediate)
        back_to_ms_url = load_form(adfs_intermediate).get('action')
        # If stays in adfs, it means that username or password is incorrect
        if not urlparse(back_to_ms_url).netloc:
            raise WrongUsernameOrPassword('Incorrect username or password.')

    # If intermediate page does not exist
    else:
        back_to_ms_url = adfs_login_form_url
        adfs_intermediate_payload = adfs_login_payload

    # Just return if told so
    if not load_page_after_login:
        return None

    # Send to Microsoft "Stay logged in?" page, and say no
    ms_confirm = session.post(back_to_ms_url, data=adfs_intermediate_payload)
    # If this page is skipped, sometimes happens
    if urlparse(ms_confirm.url).netloc != 'login.microsoftonline.com':
        return ms_confirm
    ms_confirm_CDATA = load_CDATA(ms_confirm)
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
    ms_out = session.post(ms_out_url, data=ms_confirm_payload)

    # If encounters 'Working...' page
    if ms_out.url == ms_out_url:
        return submit_form(ms_out, session=session)

    # Return page after login
    else:
        return ms_out


def psl_login(username, password, session=requests.Session()):
    """Login to Powerschool Learning.
    Returns a requests.Response instance.

    username: str,
    password: str,

    session: requests.Session, defaults to requests.Session().
    """
    # Login by Office 365 on Powerschool Learning
    psl_url = 'ykpaoschool.learning.powerschool.com'
    psl_login = session.get(
        'https://' + psl_url + '/do/oauth2/office365_login')

    # Check if already logged in
    if urlparse(psl_login.url).netloc == psl_url:
        return psl_login

    # Login through Microsoft
    return ms_login(username, password,
        session=session, redirect_to_ms=psl_login)


def office_login(username, password, session=requests.Session()):
    """Login to Microsoft Office.
    Returns a requests.Response instance.

    username: str,
    password: str,

    session: requests.Session, defaults to requests.Session().
    """
    # Login through Microsoft
    return ms_login(username, password, session=session)


def _main():
    """Internal function, Just for testing & debugging."""

    # # Username and Password
    # USERNAME, PASSWORD = load(prompt=True)
    # print()

    # session = set_up_session()
    
    # ms_login(USERNAME, PASSWORD, session=session)
    # psl_login(USERNAME, PASSWORD, session=session)
    # ms_login(USERNAME, PASSWORD, session=session)
    # ps_login(USERNAME, PASSWORD, session=session)
    # ps_login(USERNAME, PASSWORD, session=session)

    # # Login to Powerschool Learning
    # psl = psl_login(USERNAME, PASSWORD, session=session)
    # psl_page = load_soup(psl)

    print(ps_login.text)


if __name__ == '__main__':
    _main()
