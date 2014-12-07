import rethinkdb as r

from decorators import classproperty, classaccessonly, classaccessonlyproperty
from errors import OperationError
from field_handler import FieldHandlerBase, FieldHandler
from registry import model_registry
from related import ObjectSet
from utils import wrap_document, pluralize


REL_TYPES = ('has_one', 'has_many', 'belongs_to', 'has_and_belongs_to_many')


class ModelBase(type):
    def __new__(cls, name, bases, dct):
        super_new = super(ModelBase, cls).__new__

        # Ensure the following are not done for the Model class itself
        parents = [b for b in bases if isinstance(b, ModelBase)]
        if not parents:
            return super_new(cls, name, bases, dct)

        # Set metadata
        dct['_table'] = pluralize(name).lower()

        rel_attrs = {rel: dct.setdefault(rel, ()) for rel in REL_TYPES}
        dct['_field_handler_cls'] = FieldHandlerBase(
            '%sFieldHandler' % name,
            (FieldHandler,),
            dict(rel_attrs, model=name))

        new_class = super_new(cls, name, bases, dct)
        model_registry.register(name, new_class)
        return new_class


class Model(object):
    __metaclass__ = ModelBase

    def __init__(self, **kwargs):
        self.fields = self._field_handler_cls()

        for key, value in kwargs.items():
            # Assign fields this way to be sure that validation takes place
            setattr(self.fields, key, value)

    def save(self):
        fields_dict = self.fields.as_dict()
        try:
            # Attempt update
            id_ = fields_dict['id']
            result = (r.table(self._table).get(id_).replace(r.row
                        .without(r.row.keys().difference(fields_dict.keys()))
                        .merge(fields_dict), return_changes=True)
                      .run())
        except KeyError:
            # Resort to insert
            result = (r.table(self._table).insert(fields_dict, return_changes=True)
                      .run())

        if result['errors'] > 0:
            raise OperationError(result['first_error'])

        # Force overwrite so that related caches are flushed
        self.fields.__dict__ = result['changes'][0]['new_val']

    def delete(self):
        try:
            id_ = getattr(self.fields, 'id')
            result = r.table(self._table).get(id_).delete().run()
        except AttributeError:
            raise OperationError('Cannot delete %r (object not saved or '
                                 'already deleted)' % self)

        if result['errors'] > 0:
            raise OperationError(result['first_error'])

        delattr(self.fields, 'id')
        # Remove any reference to the deleted object
        for field in self.fields.related:
            delattr(self.fields, field)

    @classaccessonly
    def create(cls, **kwargs):
        obj = cls(**kwargs)
        obj.save()
        return obj

    @classaccessonly
    def get(cls, id_=None, **kwargs):
        if id_:
            doc = cls.table.get(id_).run()
            if doc is not None:
                return wrap_document(cls, doc)
            return None
        try:
            return list(ObjectSet(cls, (cls.table.filter(kwargs)
                                        .limit(1).run())))[0]
        except IndexError:
            return None

    @classaccessonly
    def get_or_create(cls, id_=None, **kwargs):
        obj = cls.get(id_, **kwargs)
        if obj:
            return obj, False
        return cls.create(**kwargs), True

    @classaccessonly
    def all(cls):
        return ObjectSet(cls, cls.table.run())

    @classaccessonly
    def filter(cls, ids=None, **kwargs):
        if ids:
            return ObjectSet(cls, (cls.table.get_all(r.args(ids))
                                   .filter(kwargs).run()))
        return ObjectSet(cls, cls.table.filter(kwargs).run())

    def __getitem__(self, key):
        try:
            return getattr(self.fields, key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        try:
            setattr(self.fields, key, value)
        except AttributeError:
            raise KeyError(key)

    def __delitem__(self, key):
        try:
            delattr(self.fields, key)
        except AttributeError:
            raise KeyError(key)

    def __contains__(self, item):
        return hasattr(self.fields, item)

    def __repr__(self):
        try:
            id_ = self.fields.id
        except AttributeError:
            id_ = 'not saved'
        return '<%s: %s>' % (self.__class__.__name__, id_)

    def __str__(self):
        return '<%s object>' % self.__class__.__name__

    @classaccessonlyproperty
    def table(cls):
        return r.table(cls._table)
