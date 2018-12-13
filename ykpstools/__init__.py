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
    'AuthPage',
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


def auth(*args, fargs=(), fkwargs={}, **kwargs):
    """A simple wrapper for
    User(*args, **kwargs).auth(*fargs, **fkwargs).
    """
    return User(*args, **kwargs).auth(*fargs, **fkwargs)


def powerschool(*args, fargs=(), fkwargs={}, **kwargs):
    """A simple wrapper for
    User(*args, **kwargs).powerschool(*fargs, **fkwargs).
    """
    return User(*args, **kwargs).powerschool(*fargs, **fkwargs)


def microsoft(*args, fargs=(), fkwargs={}, **kwargs):
    """
    A simple wrapper for
    User(*args, **kwargs).microsoft(*fargs, **fkwargs).
    """
    return User(*args, **kwargs).microsoft(*fargs, **fkwargs)


def powerschool_learning(*args, fargs=(), fkwargs={}, **kwargs):
    """
    A simple wrapper for
    User(*args, **kwargs).powerschool_learning(*fargs, **fkwargs).
    """
    return User(*args, **kwargs).powerschool_learning(*fargs, **fkwargs)
