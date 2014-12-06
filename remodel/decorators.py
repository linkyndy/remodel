class cached_property(object):
    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        # Set an instance attribute having the same name as the cached property
        # so that the descriptor won't be called again when accessing the property
        # (see how descriptors work)
        result = instance.__dict__[self.name] = self.func(instance)
        return result


class classproperty(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner=None):
        return self.func(owner)


class classaccessonlyproperty(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner=None):
        if instance is not None:
            raise AttributeError('Property "%s" is not available via "%s" instances'
                                 % (self.func.__name__, owner.__name__))
        return self.func(owner)


class classaccessonly(object):
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner=None):
        if instance is not None:
            raise AttributeError('Method is not available via %s instances'
                                 % owner.__name__)
        def newfunc(*args, **kwargs):
            return self.func(owner, *args, **kwargs)
        return newfunc


def synchronized(lock):
    def wrap(func):
        def synchronized_func(*args, **kwargs):
            with lock:
                return func(*args, **kwargs)
        return synchronized_func
    return wrap
