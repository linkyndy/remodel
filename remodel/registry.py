from collections import defaultdict

from .errors import AlreadyRegisteredError


class ModelRegistry(object):
    def __init__(self):
        self._data = {}

    def __len__(self):
        return len(self._data)

    def register(self, name, cls):
        import remodel.models

        if name in self._data:
            raise AlreadyRegisteredError('Model "%s" has been already registered' % name)
        if not issubclass(cls, remodel.models.Model):
            raise ValueError('Registered model class "%r" must be a subclass of "Model"' % cls)
        self._data[name] = cls

    def unregister(self, name):
        if name not in self._data:
            raise KeyError('"%s" is not a registered model' % name)
        del self._data[name]

    def get(self, name):
        if name not in self._data:
            raise KeyError('Model "%s" has not been registered' % name)
        return self._data[name]

    def all(self):
        return self._data

    def clear(self):
        self._data = {}


# Used by ModelBase metaclass to register every declared Model class.
model_registry = ModelRegistry()


class IndexRegistry(object):
    def __init__(self):
        self._data = defaultdict(set)

    def register(self, model, index):
        self._data[model].add(index)

    def unregister(self, model, index):
        self._data[model].discard(index)

    def get_for_model(self, model):
        if model not in self._data:
            return set()
        return self._data[model]

    def all(self):
        return self._data

    def clear(self):
        self._data = defaultdict(set)


index_registry = IndexRegistry()
