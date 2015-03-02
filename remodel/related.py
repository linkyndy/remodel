import rethinkdb as r
from inflection import tableize

from .decorators import cached_property
from .object_handler import ObjectHandler
from .registry import model_registry


class RelationDescriptor(object):
    @property
    def model_cls(self):
        return model_registry.get(self.model)


class HasOneDescriptor(RelationDescriptor):
    def __init__(self, model, lkey, rkey):
        self.model = model
        self.lkey = lkey
        self.rkey = rkey
        self.related_cache = '_%s_cache' % model.lower()

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return getattr(instance, self.related_cache)
        except AttributeError:
            instance_lkey = getattr(instance, self.lkey, None)
            if instance_lkey is None:
                rel_obj = None
            else:
                params = {self.rkey: instance_lkey}
                rel_obj = self.model_cls.get(**params)
            # Make related document available on parent (this) e.g.: user.profile
            setattr(instance, self.related_cache, rel_obj)
            return rel_obj

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, self.model_cls):
            raise ValueError('%s instance expected, got %r' % (
                            self.model_cls.__name__, value))

        if value is None:
            rel_obj = getattr(instance, self.related_cache, None)
            if rel_obj is not None:
                # We are deleting the rkey attr on related field handler, not obj
                del rel_obj.fields.__dict__[self.rkey]
        else:
            instance_lkey = getattr(instance, self.lkey, None)
            if instance_lkey is None:
                raise ValueError('Cannot assign "%r": current instance isn\'t '
                                 'saved' % value)
            # Assign field this way to skip validation
            value.fields.__dict__[self.rkey] = instance_lkey
        # Make related document available on parent (this) e.g.: user.profile
        setattr(instance, self.related_cache, value)

    def __delete__(self, instance):
        self.__set__(instance, None)


class BelongsToDescriptor(RelationDescriptor):
    def __init__(self, model, lkey, rkey):
        self.model = model
        self.lkey = lkey
        self.rkey = rkey
        self.related_cache = '_%s_cache' % model.lower()

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return getattr(instance, self.related_cache)
        except AttributeError:
            instance_lkey = instance.__dict__.get(self.lkey, None)
            if instance_lkey is None:
                rel_obj = None
            else:
                params = {self.rkey: instance_lkey}
                rel_obj = self.model_cls.get(**params)
            # Make parent document available on related (this) e.g.: profile.user
            setattr(instance, self.related_cache, rel_obj)
            return rel_obj

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, self.model_cls):
            raise ValueError('%s instance expected, got %r' % (
                            self.model_cls.__name__, value))

        if value is None:
            if self.lkey in instance.__dict__:
                del instance.__dict__[self.lkey]
        else:
            value_rkey = getattr(value.fields, self.rkey, None)
            if value_rkey is None:
                raise ValueError('Cannot assign "%r": "%s" instance isn\'t '
                                 'saved' % (value, value.__class__.__name__))
            # Assign field this way to skip validation
            instance.__dict__[self.lkey] = value_rkey
        # Make parent document available on related (this) e.g.: profile.user
        setattr(instance, self.related_cache, value)

    def __delete__(self, instance):
        self.__set__(instance, None)


def create_related_object_handler_cls(model_cls, lkey, rkey):
    class RelatedObjectHandler(ObjectHandler):
        def __init__(self, parent):
            super(RelatedObjectHandler, self).__init__(model_cls)
            # Parent field handler instance
            self.parent = parent
            self.query = self.query.get_all(self._get_parent_lkey(), index=rkey)

        def create(self, **kwargs):
            obj = super(RelatedObjectHandler, self).create(**kwargs)
            self.add(obj)
            return obj

        def get_or_create(self, id_=None, **kwargs):
            obj, created = super(RelatedObjectHandler, self).get_or_create(id_, **kwargs)
            self.add(obj)
            return obj, created

        def add(self, *objs):
            for obj in objs:
                if not isinstance(obj, model_cls):
                    raise TypeError('%s instance expected, got %r' %
                                    (model_cls.__name__, obj))
                # Assign field this way to skip validation
                obj.fields.__dict__[rkey] = self._get_parent_lkey()
                obj.save()

        def remove(self, *objs):
            ref_key = self._get_parent_lkey()
            for obj in objs:
                obj_key = obj.fields.__dict__.get(rkey, None)
                if obj_key != ref_key:
                    raise ValueError('%r is not a related object' % obj)
                del obj.fields.__dict__[rkey]
                obj.save()

        def clear(self):
            for obj in self.all():
                del obj.fields.__dict__[rkey]
                obj.save()

        def _get_parent_lkey(self):
            parent_lkey = getattr(self.parent, lkey, None)
            if parent_lkey is None:
                raise ValueError('Cannot access related "%s" set: current '
                                 'instance isn\'t saved' % model_cls.__name__)
            return parent_lkey

    return RelatedObjectHandler


class HasManyDescriptor(RelationDescriptor):
    def __init__(self, model, lkey, rkey):
        self.model = model
        self.lkey = lkey
        self.rkey = rkey
        self.related_cache = '_%s_cache' % tableize(model)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return getattr(instance, self.related_cache)
        except AttributeError:
            rel_object_handler = self.related_object_handler_cls(instance)
            # Make related set available on parent (this) e.g.: artist.songs
            setattr(instance, self.related_cache, rel_object_handler)
            return rel_object_handler

    def __set__(self, instance, value):
        rel_object_handler = self.__get__(instance)
        rel_object_handler.clear()
        rel_object_handler.add(*value)

    def __delete__(self, instance):
        rel_object_handler = self.__get__(instance)
        rel_object_handler.clear()

    @cached_property
    def related_object_handler_cls(self):
        return create_related_object_handler_cls(self.model_cls, self.lkey, self.rkey)


def create_related_m2m_object_handler_cls(model_cls, lkey, rkey, join_model_cls, mlkey, mrkey):
    class RelatedM2MObjectHandler(ObjectHandler):
        def __init__(self, parent):
            super(RelatedM2MObjectHandler, self).__init__(model_cls)
            # Parent field handler instance
            self.parent = parent
            # Returns all docs from model_cls which are referenced in join_model_cls
            self.query = (r.table(join_model_cls._table)
                          .get_all(self._get_parent_lkey(), index=mlkey)
                          .eq_join(mrkey, r.table(model_cls._table), index=rkey)
                          .map(lambda res: res['right']))

        def create(self, **kwargs):
            obj = super(RelatedM2MObjectHandler, self).create(**kwargs)
            self.add(obj)
            return obj

        def get_or_create(self, id_=None, **kwargs):
            obj, created = super(RelatedM2MObjectHandler, self).get_or_create(id_, **kwargs)
            self.add(obj)
            return obj, created

        def add(self, *objs):
            new_keys = set()
            for obj in objs:
                if not isinstance(obj, model_cls):
                    raise TypeError('%s instance expected, got %r' %
                                    (model_cls.__name__, obj))
                obj_key = getattr(obj.fields, rkey, None)
                if obj_key is None:
                    raise ValueError('Cannot add %r: the value for field %s '
                                     'is missing (try saving the object first'
                                     ')' % (obj, rkey))
                new_keys.add(obj_key)

            existing_keys = {doc[rkey]
                            for doc in self.query.run()}
            new_keys -= existing_keys

            for obj_key in new_keys:
                params = {mlkey: self._get_parent_lkey(),
                          mrkey: obj_key}
                join_model_cls.table.insert(params).run()

        def remove(self, *objs):
            old_keys = set()
            for obj in objs:
                if not isinstance(obj, model_cls):
                    raise TypeError('%s instance expected, got %r' %
                                    (model_cls.__name__, obj))
                obj_key = getattr(obj.fields, rkey, None)
                if obj_key is not None:
                    old_keys.add(obj_key)

            existing_keys = {doc[rkey]
                            for doc in self.query.run()}
            # Remove inexisting keys from old_keys
            old_keys &= existing_keys

            if old_keys:
                (join_model_cls.table.get_all(r.args(list(old_keys)), index=mrkey)
                                     .delete()
                                     .run())

        def clear(self):
            (join_model_cls.table
             .get_all(self._get_parent_lkey(), index=mlkey)
             .delete().run())

        def _get_parent_lkey(self):
            parent_lkey = getattr(self.parent, lkey, None)
            if parent_lkey is None:
                raise ValueError('Cannot access related "%s" set: current '
                                 'instance isn\'t saved' %  model_cls.__name__)
            return parent_lkey

    return RelatedM2MObjectHandler


class HasAndBelongsToManyDescriptor(RelationDescriptor):
    def __init__(self, model, lkey, rkey, join_model, mlkey, mrkey):
        self.model = model
        self.lkey = lkey
        self.rkey = rkey
        self.join_model = join_model
        self.mlkey = mlkey
        self.mrkey = mrkey
        self.related_cache = '_%s_cache' % tableize(model)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return getattr(instance, self.related_cache)
        except AttributeError:
            rel_m2m_object_handler = self.related_m2m_object_handler_cls(instance)
            # Make related set available on parent (this) e.g.: user.artists
            setattr(instance, self.related_cache, rel_m2m_object_handler)
            return rel_m2m_object_handler

    def __set__(self, instance, value):
        rel_m2m_object_handler = self.__get__(instance)
        rel_m2m_object_handler.clear()
        rel_m2m_object_handler.add(*value)

    def __delete__(self, instance):
        rel_m2m_object_handler = self.__get__(instance)
        rel_m2m_object_handler.clear()

    @cached_property
    def related_m2m_object_handler_cls(self):
        return create_related_m2m_object_handler_cls(
            self.model_cls, self.lkey, self.rkey,
            self.join_model_cls, self.mlkey, self.mrkey)

    @property
    def join_model_cls(self):
        return model_registry.get(self.join_model)
