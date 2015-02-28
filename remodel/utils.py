from inflection import pluralize, underscore
from threading import Lock
from warnings import warn
from .decorators import synchronized


def tableize(what):
    return pluralize(underscore(what))


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
