from rethinkdb import r


def create_tables():
    from .registry import model_registry

    created_tables = r.table_list().run()
    for model_cls in model_registry.all().values():
        if model_cls.table_name not in created_tables:
            result = r.table_create(model_cls.table_name).run()
            if result['tables_created'] != 1:
                raise RuntimeError('Could not create table %s for model %s' % (
                                   model_cls.table_name, model_cls.__name__))


def drop_tables():
    from .registry import model_registry

    created_tables = r.table_list().run()
    for model_cls in model_registry.all().values():
        if model_cls.table_name in created_tables:
            result = r.table_drop(model_cls.table_name).run()
            if result['tables_dropped'] != 1:
                raise RuntimeError('Could not drop table %s for model %s' % (
                                   model_cls.table_name, model_cls.__name__))


def create_indexes():
    from .registry import model_registry, index_registry

    for model, index_set in index_registry.all().items():
        model_cls = model_registry.get(model)
        created_indexes = r.table(model_cls.table_name).index_list().run()
        for index in index_set:
            if index not in created_indexes:
                result = r.table(model_cls.table_name).index_create(index).run()
                if result['created'] != 1:
                    raise RuntimeError('Could not create index %s for table %s' % (
                                       index, model_cls.table_name))
        r.table(model_cls.table_name).index_wait().run()
