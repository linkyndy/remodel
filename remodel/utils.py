import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError
from inflection import pluralize, underscore
from threading import Lock
from warnings import warn

import connection
from decorators import synchronized


def tableize(what):
    return pluralize(underscore(what))


def create_tables():
    from registry import model_registry
    for model_cls in model_registry.all().itervalues():
        try:
            result = r.table_create(model_cls._table).run()
        except RqlRuntimeError:
            raise RuntimeError('Table %s for model %s already created'
                               % (model_cls._table, model_cls.__name__))
        assert (result['created'] != 1,
                'Could not create table %s for model %s' % (model_cls._table,
                                                            model_cls.__name__))

def create_indexes():
    from registry import model_registry, index_registry
    for model, index_set in index_registry.all().iteritems():
        model_cls = model_registry.get(model)
        for index in index_set:
            r.table(model_cls._table).index_create(index).run()
        r.table(model_cls._table).index_wait().run()
        assert (set(r.table(model_cls._table).index_list().run()) ==
                index_set,
                'Could not create all indexes for table %s' % model_cls._table)


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
