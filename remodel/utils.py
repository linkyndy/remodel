import rethinkdb as r
from rethinkdb.errors import RqlRuntimeError

from registry import model_registry, index_registry


def wrap_document(model_cls, doc):
    obj = model_cls()
    # Assign fields this way to skip validation
    obj.fields.__dict__ = doc
    return obj


def pluralize(what):
    import inflect
    p = inflect.engine()
    return p.plural(what)


def singularize(what):
    import inflect
    p = inflect.engine()
    return p.singular(what)


def create_tables():
    for model_cls in model_registry.all().itervalues():
        try:
            result = r.table_create(model_cls._table).run(model_cls.conn)
        except RqlRuntimeError:
            raise RuntimeError('Table %s for model %s already created'
                               % (model_cls._table, model_cls.__name__))
        assert (result['created'] != 1,
                'Could not create table %s for model %s' % (model_cls._table,
                                                            model_cls.__name__))

def create_indexes():
    for model, index_set in index_registry.all().iteritems():
        model_cls = model_registry.get(model)
        for index in index_set:
            r.table(model_cls._table).index_create(index).run(model_cls.conn)
        r.table(model_cls._table).index_wait().run(model_cls.conn)
        assert (set(r.table(model_cls._table).index_list().run(model_cls.conn)) ==
                index_set,
                'Could not create all indexes for table %s' % model_cls._table)
