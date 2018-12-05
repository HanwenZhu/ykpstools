"""Tools & Utilities associated with online logins of YKPS."""

__all__ = ['Error', 'LoginConnectionError', 'WrongUsernameOrPassword',
    'GetUsernamePasswordError', 'GetIPError', 'User', 'Page', 'ps_login',
    'ms_login', 'psl_login']
__author__ = 'Thomas Zhu'

from .exceptions import *
from .page import *
from .user import *


def auth(*args, **kwargs):
    """A simple wrapper for User(*args, **kwargs).auth()."""
    return User(*args, **kwargs).auth()


def ps_login(*args, **kwargs):
    """A simple wrapper for User(*args, **kwargs).ps_login()."""
    return User(*args, **kwargs).ps_login()


def ms_login(*args, **kwargs):
    """A simple wrapper for User(*args, **kwargs).ms_login()."""
    return User(*args, **kwargs).ms_login()


def psl_login(*args, **kwargs):
    """A simple wrapper for User(*args, **kwargs).psl_login()."""
    return User(*args, **kwargs).psl_login()
