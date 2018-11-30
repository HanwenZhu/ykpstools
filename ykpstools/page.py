"""Class 'Page' is a wrapper around requests.models.Response with
convenient functions.

response: a requests.models.Response instance.
"""

__all__ = ['Page']

import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

class Page:

    """Class 'Page' is a wrapper around requests.models.Response with
    convenient functions.
    
    response: a requests.models.Response instance.
    """

    def __init__(self, user, response, *args, **kwargs):
        """Initialize a Page.

        response: requests.models.Response"""
        self.response = response
        self.response.encoding = 'utf-8'
        self.user = user

    def url(self):
        """Get current URL."""
        return urlparse(self.response.url)

    def text(self):
        """Returns response text."""
        return self.response.text

    def soup(self, features='lxml', *args, **kwargs):
        """Returns bs4.BeautifulSoup of this page.

        *args, **kwargs: arguments for BeautifulSoup.
        """
        return BeautifulSoup(self.text(), features=features, *args, **kwargs)

    def CDATA(self):
        """Gets the CDATA of this page."""
        expression = re.compile(r'//<!\[CDATA\[\n\$Config=(.*);\n//\]\]>')
        return json.loads(expression.findall(
            self.soup().find(text=expression).string)[0])

    def form(self, *find_args, **find_kwargs):
        """Gets HTML element form as bs4.element.Tag of this page.

        *find_args, **find_kwargs: arguments for BeautifulSoup.find('form').
        """
        return self.soup().find('form', *find_args, **find_kwargs)

    def payload(self, updates={}, *find_args, **find_kwargs):
        """Load completed form of this page.

        updates: updates to payload,
        *find_args, **find_kwargs: arguments for BeautifulSoup.find('form').
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
        *find_args, **find_kwargs: arguments for BeautifulSoup.find('form').
        """
        form = self.form()
        if form is None:
            return self
        else:
            method = form.get('method')
            action = form.get('action')
            if action.startswith('/'):
                url = self.url()
                action = url.scheme + '://' + url.netloc + action
            return self.user.request(method, action,
                data=self.payload(updates, *find_args, **find_kwargs))

    def json(self):
        """Returns response in json format."""
        return self.response.json()
