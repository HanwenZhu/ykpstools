"""Tools & Utilities associated with online logins of YKPS."""

__all__ = [
    'Error',
    'LoginConnectionError',
    'WrongUsernameOrPassword',
    'GetUsernamePasswordError',
    'GetIPError',
    'User',
    'Page',
    'LoginPageBase',
    'PowerschoolPage',
    'MicrosoftPage',
    'PowerschoolLearningPage',
    'auth',
    'powerschool',
    'microsoft',
    'powerschool_learning',
]
__author__ = 'Thomas Zhu'

from ykpstools.exceptions import *
from ykpstools.page import *
from ykpstools.user import *


def auth(*args, **kwargs):
    """A simple wrapper for User(*args, **kwargs).auth()."""
    return User(*args, **kwargs).auth()


def powerschool(*args, **kwargs):
    """A simple wrapper for User(*args, **kwargs).powerschool()."""
    return User(*args, **kwargs).powerschool()


def microsoft(redirect_to_ms=None, *args, **kwargs):
    """A simple wrapper for User(*args, **kwargs).microsoft(redirect_to_ms)."""
    return User(*args, **kwargs).microsoft(redirect_to_ms)


def powerschool_learning(*args, **kwargs):
    """A simple wrapper for User(*args, **kwargs).powerschool_learning()."""
    return User(*args, **kwargs).powerschool_learning()
