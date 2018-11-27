"""Utilities for general web rendering, parsing, etc."""

import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


def set_up_session():
    """Set up a session"""
    session = requests.Session()
    UA = ' '.join((
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6)',
        'AppleWebKit/537.36 (KHTML, like Gecko)',
        'Chrome/69.0.3497.100',
        'Safari/537.36',
    ))
    session.headers.update({'User-Agent': UA})
    return session


def load_text(resp):
    """Load text from html or requests.Response"""
    if isinstance(resp, str):
        return resp
    elif isinstance(resp, requests.Response):
        resp.encoding = 'utf-8'
        return resp.text
    else:
        raise TypeError("Type of 'resp' unsupported.")


def load_soup(resp):
    """Load bs4.BeautifulSoup from html or requests.Response"""
    return BeautifulSoup(load_text(resp), features='lxml')


def load_CDATA(resp):
    """Load CDATA from html or requests.Response"""
    CDATA = json.loads(
        re.compile(
            r'//<!\[CDATA\[\n\$Config=(.*);\n//\]\]>'
        ).findall(
            load_soup(resp).find(
                text=re.compile(r'//<!\[CDATA\[.*')
            ).string
        )[0]
    )
    return CDATA


def load_form(resp, *find_args, **find_kwargs):
    """Load form from html or requests.Response"""
    return load_soup(resp).find('form', *find_args, **find_kwargs)


def load_payload(resp, updates={}, *find_args, **find_kwargs):
    """Load completed form from html or requests.Response"""
    payload = {
        i.get('name'): i.get('value')
        for i in load_form(resp).find_all('input')
        if i is not None
    }
    payload.update(updates)
    return payload


def submit_form(session, resp, updates={}, *find_args, **find_kwargs):
    """Submit form from html or requests.Response"""
    form = load_form(resp)
    method = form.get('method')
    action = form.get('action')
    if action.startswith('/'):
        url = urlparse(resp.url)
        action = url.scheme + '://' + url.netloc + action
    return session.request(
        method, action,
        data=load_payload(resp, updates, *find_args, **find_kwargs)
    )
