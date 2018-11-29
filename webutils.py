"""Utilities for general web rendering, parsing, etc."""

from os import popen
from socket import gethostbyname, gethostname, getfqdn
from uuid import UUID, getnode
import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from exceptions import GetIPError

all_methods = (
    'GET', 'HEAD', 'POST', 'PUT',
    'DELETE', 'CONNECT', 'OPTIONS',
    'TRACE', 'PATCH',
)


def get_IP():
    """Returns private IP address."""
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
    return IP


def get_MAC():
    """Returns MAC address."""
    MAC = ':'.join([UUID(int=getnode()).hex[-12:].upper()[i:i+2]
        for i in range(0, 11, 2)])
    return MAC


def set_up_session(*args, **kwargs):
    """Set up a session.

    args, kwargs: args and kwargs for requests.Session.
    """
    session = requests.Session(*args, **kwargs)
    session.headers.update(
        {'User-Agent': ' '.join((
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6)',
            'AppleWebKit/537.36 (KHTML, like Gecko)',
            'Chrome/69.0.3497.100',
            'Safari/537.36',
    ))})
    return session


def load_text(response):
    """Load text from html or requests.Response.

    response: str as html or requests.Response.
    """
    if isinstance(response, str):
        return response
    elif isinstance(response, requests.Response):
        response.encoding = 'utf-8'
        return response.text
    else:
        raise TypeError("Type of 'response' unsupported.")


def load_soup(response):
    """Load bs4.BeautifulSoup from html or requests.Response.

    response: str as html or requests.Response.
    """
    return BeautifulSoup(load_text(response), features='lxml')


def load_CDATA(response):
    """Load CDATA from html or requests.Response.

    response: str as html or requests.Response.
    """
    expression = re.compile(r'//<!\[CDATA\[\n\$Config=(.*);\n//\]\]>')
    return json.loads(expression.findall(
        load_soup(response).find(text=expression).string)[0])


def load_form(response, *find_args, **find_kwargs):
    """Load form from html or requests.Response.

    response: str as html or requests.Response,

    find_args, find_kwargs: args and kwargs for BeautifulSoup.find('form').
    """
    return load_soup(response).find('form', *find_args, **find_kwargs)


def load_payload(response, updates={}, *find_args, **find_kwargs):
    """Load completed form from html or requests.Response.

    response: str as html or requests.Response,

    updates: updates to payload,
    find_args, find_kwargs: args and kwargs for BeautifulSoup.find('form').
    """
    payload = {
        i.get('name'): i.get('value')
        for i in load_form(response).find_all('input') if i is not None}
    payload.update(updates)
    return payload


def submit_form(response, session=requests.Session(),
    updates={}, *find_args, **find_kwargs):
    """Submit form from html or requests.Response.

    response: str as html or requests.Response,

    session: session for form request,
    updates: updates to payload,
    find_args, find_kwargs: args and kwargs for BeautifulSoup.find('form').
    """
    form = load_form(response)
    method = form.get('method')
    action = form.get('action')
    if action.startswith('/'):
        url = urlparse(response.url)
        action = url.scheme + '://' + url.netloc + action
    return session.request(method, action,
        data=load_payload(response, updates, *find_args, **find_kwargs))    
