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

from exceptions import GetIPError


def get_IP_MAC():
    # Get Private IP Address and MAC Address
    try:
        IP = gethostbyname(gethostname())
    except Exception:
        try:
            IP = gethostbyname(getfqdn())
        except Exception:
            IP = popen("ifconfig | grep 'inet ' | grep -v '127.0' | xargs "
                "| awk -F '[ :]' '{print $2}'").readline().strip()
            if not IP:
                raise GetIPError("Can't retrieve IP address.")
    MAC = ':'.join([UUID(int=getnode()).hex[-12:].upper()[i:i+2]
        for i in range(0,11,2)])

    return IP, MAC


def login_webauth(session, username, password):
    """Web Authentication"""
    url = 'https://auth.ykpaoschool.cn/portalAuthAction.do'
    IP, MAC = get_IP_MAC()
    form_data = {
        'wlanuserip': IP,
        'mac': MAC,
        'wlanacname': 'hh1u6p',
        'wlanacIp': '192.168.186.2',
        'userid': username,
        'passwd': password
    }
    session.post(url, data=form_data, verify=False)


def login_blueauth(session, username, password):
    """The Blue Auth Page"""
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


def auth(session):
    login_webauth(session)
    login_blueauth(session)
