"""Tools to authorize into school Wi-Fi."""

# Derived from: https://github.com/yu-george/AutoAuth-YKPS/
__author__ = 'George Yu'
__version__ = '3.1.5'

from os import system, popen, path
from sys import version_info
from socket import gethostbyname, gethostname, getfqdn
from uuid import UUID, getnode
from urllib.parse import unquote
from base64 import b64decode
import re

import requests

from exceptions import GetIPError
from webutils import get_IP, get_MAC


def _login_webauth(username, password, session=requests.Session(),
                   IP=get_IP(), MAC=get_MAC(), **_):
    """Internal function. Web Authentication."""
    url = 'https://auth.ykpaoschool.cn/portalAuthAction.do'
    form_data = {
        'wlanuserip': IP,
        'mac': MAC,
        'wlanacname': 'hh1u6p',
        'wlanacIp': '192.168.186.2',
        'userid': username,
        'passwd': password
    }
    session.post(url, data=form_data, verify=False)


def _login_blueauth(username, password, session=requests.Session(), **_):
    """Internal function. The Blue Auth Page."""
    # Get authServ and oldURL
    web = s.get('http://www.apple.com/cn/',
        allow_redirects=True, headers=headers)
    oldURL_and_authServ = re.compile(
        r'oldURL=([^&]+)&authServ=(.+)').findall(unquote(web.url))
    if oldURL_and_authServ:
        oldURL, authServ = oldURL_and_authServ[0]
    else:
        return

    # Login
    url = 'http://192.168.1.1:8181/'
    form_data = {
        'txtUserName': username,
        'txtPasswd': password,
        'oldURL': oldURL,
        'authServ': authServ
    }
    session.post(url, data=form_data, verify=False)


def auth(username, password, *args, **kwargs):
    """Takes session and logins to Wi-Fi.

    username, password: str, str,

    session: requests.Session, the session to authorize with,
             defaults to requests.Session().
    """
    _login_webauth(username, password, *args, **kwargs)
    _login_blueauth(username, password, *args, **kwargs)
