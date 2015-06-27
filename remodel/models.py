import rethinkdb as r
from six import add_metaclass
from inflection import tableize

from .decorators import callback, classaccessonlyproperty, dispatch_to_metaclass
from .errors import OperationError
from .field_handler import FieldHandlerBase, FieldHandler
from .object_handler import ObjectHandler
from .registry import model_registry
from .utils import deprecation_warning


REL_TYPES = ('has_one', 'has_many', 'belongs_to', 'has_and_belongs_to_many')
CALLBACKS = ('before_save', 'after_save', 'before_delete', 'after_delete', 'after_init')


class ModelBase(type):
    def __new__(mcs, name, bases, dct):
        super_new = super(ModelBase, mcs).__new__

        # Ensure the following are not done for the Model class itself
        parents = [b for b in bases if isinstance(b, ModelBase)]
        if not parents:
            return super_new(mcs, name, bases, dct)

        # Set metadata
        dct['_table'] = tableize(name)

        rel_attrs = {rel: dct.setdefault(rel, ()) for rel in REL_TYPES}
        dct['_field_handler_cls'] = FieldHandlerBase(
            '%sFieldHandler' % name,
            (FieldHandler,),
            dict(rel_attrs, model=name))
        object_handler_cls = dct.setdefault('object_handler', ObjectHandler)

        # Register callbacks
        dct['_callbacks'] = {callback: [] for callback in CALLBACKS}
        for callback in CALLBACKS:
            # Callback-named methods
            if callback in dct:
                dct['_callbacks'][callback].append(callback)
            # Callback-decorated methods
            dct['_callbacks'][callback].extend([key
                                                for key, value in dct.items()
                                                if hasattr(value, callback)])

        new_class = super_new(mcs, name, bases, dct)
        model_registry.register(name, new_class)
        setattr(new_class, 'objects', object_handler_cls(new_class))
        return new_class

    # Proxies undefined attributes to Model.objects; useful for building
    # ReQL queries directly on the Model (e.g.: User.order_by('name').run())
    def __getattr__(self, name):
        return getattr(self.objects, name)


@add_metaclass(ModelBase)
class Model(object):
    def __init__(self, **kwargs):
        self.fields = self._field_handler_cls()

        for key, value in kwargs.items():
            # Assign fields this way to be sure that validation takes place
            setattr(self.fields, key, value)

        self._run_callbacks('after_init')

    def save(self):
        self._run_callbacks('before_save')

        fields_dict = self.fields.as_dict()
        try:
            # Attempt update
            id_ = fields_dict['id']
            result = (r.table(self._table).get(id_).replace(r.row
                        .without(r.row.keys().difference(list(fields_dict.keys())))
                        .merge(fields_dict), return_changes='always').run())

        except KeyError:
            # Resort to insert
            result = (r.table(self._table).insert(fields_dict, return_changes=True)
                      .run())

        if result['errors'] > 0:
            raise OperationError(result['first_error'])

        # Force overwrite so that related caches are flushed
        self.fields.__dict__ = result['changes'][0]['new_val']

        self._run_callbacks('after_save')

    def update(self, **kwargs):
        for key, value in kwargs.items():
            # Assign fields this way to be sure that validation takes place
            setattr(self.fields, key, value)

        self.save()

    def delete(self):
        self._run_callbacks('before_delete')

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

        self._run_callbacks('after_delete')

    # TODO: Get rid of this nasty decorator after renaming .get() on ObjectHandler
    @dispatch_to_metaclass
    def get(self, key, default=None):
        try:
            return getattr(self.fields, key)
        except AttributeError:
            return default

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

    def _run_callbacks(self, name):
        for callback in self._callbacks[name]:
            getattr(self, callback)()

    @classaccessonlyproperty
    def table(self):
        deprecation_warning('Model.table will be deprecated soon. Please use '
                            'Model.objects to build any custom query on a '
                            'Model\'s table (read more about ObjectHandler)')
        return self.objects


before_save = callback('before_save')
after_save = callback('after_save')
before_delete = callback('before_delete')
after_delete = callback('after_delete')
after_init = callback('after_init')
