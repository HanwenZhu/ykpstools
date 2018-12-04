"""Class 'Page' is a wrapper around requests.Response with convenient
functions.
"""

__all__ = ['Page']
__author__ = 'Thomas Zhu'

import functools
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

    @functools.wraps(BeautifulSoup)
    def soup(self, features='lxml', *args, **kwargs):
        """Returns bs4.BeautifulSoup of this page.

        features='lxml': 'features' argument for BeautifulSoup,
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
        payload = {
            i.get('name'): i.get('value')
            for i in self.form(
                *find_args, **find_kwargs).find_all('input')
            if i.get('name') is not None}
        payload.update(updates)
        return payload

    def submit(self, updates={}, *find_args, **find_kwargs):
        """Submit form from page.
        
        updates: updates to payload,
        *find_args: arguments for BeautifulSoup.find('form'),
        **find_kwargs: keyword arguments for BeautifulSoup.find('form').
        """
        form = self.form()
        if form is None:
            return self
        else:
            method = form.get('method')
            action = urljoin(self.url().geturl(), form.get('action'))
            return self.user.request(method, action,
                data=self.payload(updates, *find_args, **find_kwargs))

    @functools.wraps(requests.Response.json)
    def json(self, *args, **kwargs):
        """Returns response in json format.

        *args: arguments for requests.Response.json,
        *kwargs: keyword arguments for requests.Response.json.
        """
        return self.response.json(*args, **kwargs)
