"""Login tools for various websites."""

import json
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from exceptions import (
    WrongUsernameOrPassword, GetUsernamePasswordError)
from creds import load
from webutils import (
    set_up_session, load_text, load_soup, load_CDATA, load_form, load_payload,
    submit_form)


def ps_login(session, username, password):
    """Login to Powerschool.
    Returns a requests.Response instance.

    session: requests.Session,
    username: str,
    password: str,
    """
    # Request login page to Powerschool
    ps_login = session.get(
        'https://powerschool.ykpaoschool.cn/public/home.html')

    # Parse login page and send login form
    return submit_form(session, ps_login,
        updates={
            'account': username,
            'pw': password
        },
        id='LoginForm'
    )


def ms_login(session, username, password, ms_login_page=None,
             load_page_after_login=True):
    """Login to Microsoft Office365.
    Returns a requests.Response instance.

    session: requests.Session,
    username: str,
    password: str,
    ms_login_page: requests.Response or str, defaults to MS login,
    load_page_after_login: load page after login, for debugging.
    """
    # Default if page not specified
    if ms_login_page is None:
        ms_login_page = session.get('https://login.microsoftonline.com/')


    # If already logged in to Microsoft Office365
    if len(load_text(ms_login_page).splitlines()) == 1:
        return submit_form(session, ms_login_page)

    # Fetch necessary stuff for GetCredentialType
    ms_dict = load_CDATA(ms_login_page)
    flowToken = ms_dict['sFT']
    originalRequest = ms_dict['sCtx']

    # Get credential type of Microsoft login
    ms_login_payload = {
        'username': username + '@ykpaoschool.cn',
        'isOtherIdpSupported': True,
        'checkPhones': False,
        'isRemoteNGCSupported': False,
        'isCookieBannerShown': False,
        'isFidoSupported': False,
        'originalRequest': originalRequest,
        'country': 'CN',
        'flowToken': flowToken,
    }
    req_ms_login = session.post(
        'https://login.microsoftonline.com'
        '/common/GetCredentialType?mkt=en-US',
        data=json.dumps(ms_login_payload)
    ).json()

    # Redirect to organization page (https://adfs.ykpaoschool.cn)
    adfs_url = req_ms_login['Credentials']['FederationRedirectUrl']
    adfs_req = session.get(adfs_url)

    # Load form to intermediate page
    adfs_login_payload = load_payload(adfs_req, updates={
        'ctl00$ContentPlaceHolder1$UsernameTextBox': username,
        'ctl00$ContentPlaceHolder1$PasswordTextBox': password,
    })
    adfs_form_url = load_form(adfs_req).get('action')

    # If intermediate page exists
    if adfs_form_url.startswith('/'):
        adfs_form_url = 'https://adfs.ykpaoschool.cn' + adfs_form_url

        # Post to intermediate page
        adfs_req_contd = session.post(adfs_form_url, data=adfs_login_payload)

        # Load form back to Microsoft login page
        adfs_login_payload_contd = load_payload(adfs_req_contd)
        back_to_ms_url = load_form(adfs_req_contd).get('action')

        # Check if valid
        if not urlparse(back_to_ms_url).netloc:
            raise WrongUsernameOrPassword('Incorrect username or password.')

    # If intermediate page does not exist
    else:
        back_to_ms_url = adfs_form_url
        adfs_login_payload_contd = adfs_login_payload

    # Just return if told so
    if not load_page_after_login:
        return None

    # Send back to Microsoft login page
    back_to_ms = session.post(back_to_ms_url, data=adfs_login_payload_contd)

    # Load Microsoft "Stay logged in?" page
    # and fetch necessary stuff to proceed
    # If this page is skipped, sometimes happens
    if urlparse(back_to_ms.url).netloc != 'login.microsoftonline.com':
        return back_to_ms
    ms_back_dict = load_CDATA(back_to_ms)
    back_ctx = ms_back_dict['sCtx']
    back_hpgrequestid = ms_back_dict['sessionId']
    back_flowToken = ms_back_dict['sFT']
    back_canary = ms_back_dict['canary']

    # Tell Microsoft login not to stay logged in
    # (will 302 redirect back)
    ms_final_post_payload = {
        'LoginOptions': 0,
        'ctx': back_ctx,
        'hpgrequestid': back_hpgrequestid,
        'flowToken': back_flowToken,
        'canary': back_canary,
        'i2': None,
        'i17': None,
        'i18': None,
        'i19': 66306,
    }
    ms_out_url = 'https://login.microsoftonline.com/kmsi'
    ms_out_page = session.post(
        ms_out_url,
        data=ms_final_post_payload
    )

    # If encounters 'Working...' page
    if ms_out_page.url == ms_out_url:
        return submit_form(session, ms_out_page)

    # Return page after login
    else:
        return ms_out_page


def psl_login(session, username, password):
    """Login to Powerschool Learning.
    Returns a requests.Response instance.

    session: requests.Session,
    username: str,
    password: str,
    """
    psl_url = 'ykpaoschool.learning.powerschool.com'

    # Login by Office 365 on Powerschool Learning
    # (will 302 redirect to MS login)
    psl_to_ms = session.get('https://' + psl_url
        + '/do/oauth2/office365_login')

    # Check if already logged in
    if urlparse(psl_to_ms.url).netloc == psl_url:
        return psl_to_ms

    # Login through Microsoft
    ms_to_psl = ms_login(
        session, username, password,
        ms_login_page=psl_to_ms)

    # Return page after login
    return ms_to_psl


def office_login(session, username, password):
    """Login to Microsoft Office.
    Returns a requests.Response instance.

    session: requests.Session,
    username: str,
    password: str,
    """
    # Login through Microsoft
    return ms_login(
        session, username, password)


def _main():
    """Just for testing & debugging"""

    # Username and Password    
    USERNAME, PASSWORD = load(prompt=True)
    print()

    session = set_up_session()
    
    ms_login(session, USERNAME, PASSWORD)
    psl_login(session, USERNAME, PASSWORD)
    ms_login(session, USERNAME, PASSWORD)
    ps_login(session, USERNAME, PASSWORD)
    ps_login(session, USERNAME, PASSWORD)

    # Login to Powerschool Learning
    ms_to_psl = psl_login(session, USERNAME, PASSWORD)
    psl_page = load_soup(ms_to_psl)


if __name__ == '__main__':
    _main()
