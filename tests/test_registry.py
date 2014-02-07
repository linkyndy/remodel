from collections import defaultdict
import pytest

from remodel.errors import AlreadyRegisteredError
from remodel.models import Model
from remodel.registry import ModelRegistry, IndexRegistry

from . import BaseTestCase


class ModelRegistryTests(BaseTestCase):
    def setUp(self):
        super(ModelRegistryTests, self).setUp()
        self.mr = ModelRegistry()

        class Artist(Model):
            pass
        self.Artist = Artist

    def test_register(self):
        self.mr.register('Artist', self.Artist)
        assert 'Artist' in self.mr._data
        assert self.mr._data['Artist'] is self.Artist

    def test_already_registered(self):
        self.mr.register('Artist', self.Artist)
        with pytest.raises(AlreadyRegisteredError):
            self.mr.register('Artist', self.Artist)

    def test_register_invalid(self):
        with pytest.raises(ValueError):
            self.mr.register('Artist', object)

    def test_unregister(self):
        self.mr.register('Artist', self.Artist)
        self.mr.unregister('Artist')
        assert 'Artist' not in self.mr._data

    def test_unregister_invalid(self):
        with pytest.raises(KeyError):
            self.mr.unregister('Artist')

    def test_unregister_unregistered(self):
        self.mr.register('Artist', self.Artist)
        self.mr.unregister('Artist')
        with pytest.raises(KeyError):
            self.mr.unregister('Artist')

    def test_get(self):
        self.mr.register('Artist', self.Artist)
        assert self.mr.get('Artist') is self.Artist

    def test_get_invalid(self):
        with pytest.raises(KeyError):
            self.mr.get('Artist')

    def test_all(self):
        self.mr.register('Artist', self.Artist)
        assert self.mr.all() == {'Artist': self.Artist}

    def test_clear(self):
        self.mr.register('Artist', self.Artist)
        self.mr.clear()
        assert self.mr._data == {}


class IndexRegistryTests(BaseTestCase):
    def setUp(self):
        super(IndexRegistryTests, self).setUp()
        self.ir = IndexRegistry()

    def test_register(self):
        self.ir.register('Artist', 'person_id')
        assert 'Artist' in self.ir._data
        assert self.ir._data['Artist'] == set(['person_id'])

    def test_register_same(self):
        self.ir.register('Artist', 'person_id')
        self.ir.register('Artist', 'person_id')
        assert 'Artist' in self.ir._data
        assert self.ir._data['Artist'] == set(['person_id'])

    def test_unregister(self):
        self.ir.register('Artist', 'person_id')
        self.ir.unregister('Artist', 'person_id')
        assert 'Artist' in self.ir._data
        assert self.ir._data['Artist'] == set()

    def test_unregister_same(self):
        self.ir.register('Artist', 'person_id')
        self.ir.unregister('Artist', 'person_id')
        self.ir.unregister('Artist', 'person_id')
        assert 'Artist' in self.ir._data
        assert self.ir._data['Artist'] == set()

    def test_get_for_model(self):
        self.ir.register('Artist', 'person_id')
        assert self.ir.get_for_model('Artist') == set(['person_id'])

    def test_get_for_inexistent_model(self):
        assert self.ir.get_for_model('Artist') == set()

    def test_get_for_unregistered_model(self):
        self.ir.register('Artist', 'person_id')
        self.ir.unregister('Artist', 'person_id')
        assert self.ir.get_for_model('Artist') == set()

    def test_get_all(self):
        self.ir.register('Artist', 'person_id')
        assert self.ir.all() == defaultdict(set, Artist=set(['person_id']))

    def test_clear(self):
        self.ir.register('Artist', 'person_id')
        self.ir.clear()
        assert self.ir._data == defaultdict(set)
