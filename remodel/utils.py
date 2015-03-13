from threading import Lock
from warnings import warn
from .decorators import synchronized


def create_tables():
    from .helpers import create_tables as ct
    deprecation_warning('remodel.utils.create_tables will be deprecated soon. '
                        'Please use remodel.helpers.create_tables instead.')
    ct()


def create_indexes():
    from .helpers import create_indexes as ci
    deprecation_warning('remodel.utils.create_indexes will be deprecated soon. '
                        'Please use remodel.helpers.create_indexes instead.')
    ci()


class Counter(object):
    lock = Lock()

    def __init__(self, init=0):
        self.n = init

    @synchronized(lock)
    def incr(self):
        self.n += 1

    @synchronized(lock)
    def decr(self):
        self.n -= 1

    @synchronized(lock)
    def current(self):
        return self.n


def deprecation_warning(message):
    warn(message, DeprecationWarning, stacklevel=2)
