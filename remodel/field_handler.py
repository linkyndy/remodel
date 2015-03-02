from inflection import tableize

from .errors import AlreadyRegisteredError
import remodel.models
from .registry import index_registry
from .related import (HasOneDescriptor, BelongsToDescriptor, HasManyDescriptor,
                     HasAndBelongsToManyDescriptor)


class FieldHandlerBase(type):
    def __new__(cls, name, bases, dct):
        if not all(isinstance(dct[rel_type], tuple) for rel_type in remodel.models.REL_TYPES):
            raise ValueError('Related models must be passed as a tuple')

        # TODO: Find a way to pass model class to its field handler class
        model = dct.pop('model')
        dct['restricted'], dct['related'] = set(), set()
        for rel in dct.pop('has_one'):
            if isinstance(rel, tuple):
                # 4-tuple relation supplied
                other, field, lkey, rkey = rel
            else:
                # Just the related model supplied
                other = rel
                field, lkey, rkey = other.lower(), 'id', '%s_id' % model.lower()
            dct[field] = HasOneDescriptor(other, lkey, rkey)
            dct['related'].add(field)
            index_registry.register(other, rkey)
        for rel in dct.pop('belongs_to'):
            if isinstance(rel, tuple):
                other, field, lkey, rkey = rel
            else:
                other = rel
                field, lkey, rkey = other.lower(), '%s_id' % other.lower(), 'id'
            dct[field] = BelongsToDescriptor(other, lkey, rkey)
            dct['related'].add(field)
            dct['restricted'].add(lkey)
            index_registry.register(model, lkey)
        for rel in dct.pop('has_many'):
            if isinstance(rel, tuple):
                other, field, lkey, rkey = rel
            else:
                other = rel
                field, lkey, rkey = tableize(other), 'id', '%s_id' % model.lower()
            dct[field] = HasManyDescriptor(other, lkey, rkey)
            dct['related'].add(field)
            index_registry.register(other, rkey)
        for rel in dct.pop('has_and_belongs_to_many'):
            if isinstance(rel, tuple):
                other, field, lkey, rkey = rel
            else:
                other = rel
                field, lkey, rkey = tableize(other), 'id', 'id'
            join_model = '_' + ''.join(sorted([model, other]))
            try:
                remodel.models.ModelBase(join_model, (remodel.models.Model,), {})
            except AlreadyRegisteredError:
                # HABTM join_model model has been registered, probably from the
                # other end of the relation
                pass
            mlkey, mrkey = '%s_id' % model.lower(), '%s_id' % other.lower()
            dct[field] = HasAndBelongsToManyDescriptor(other, lkey, rkey, join_model, mlkey, mrkey)
            dct['related'].add(field)
            index_registry.register(join_model, mlkey)
            index_registry.register(join_model, mrkey)

        return super(FieldHandlerBase, cls).__new__(cls, name, bases, dct)


class FieldHandler(object):
    def __getattribute__(self, name):
        if name in super(FieldHandler, self).__getattribute__('restricted'):
            raise AttributeError('Cannot access %s: field is restricted' % name)
        return super(FieldHandler, self).__getattribute__(name)

    def __setattr__(self, name, value):
        if name in self.restricted:
            raise AttributeError('Cannot set %s: field is restricted' % name)
        super(FieldHandler, self).__setattr__(name, value)

    def __delattr__(self, name):
        if name in self.restricted:
            raise AttributeError('Cannot delete %s: field is restricted' % name)
        super(FieldHandler, self).__delattr__(name)

    def as_dict(self):
        return {field: self.__dict__[field] for field in self.__dict__
                if not field.startswith('_')}
