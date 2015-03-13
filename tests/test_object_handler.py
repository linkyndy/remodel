import pytest
import rethinkdb as r
import unittest

from remodel.connection import get_conn
from remodel.errors import OperationError
from remodel.helpers import create_tables, create_indexes
from remodel.models import Model
from remodel.object_handler import ObjectHandler, ObjectSet
from remodel.registry import model_registry
from remodel.related import (HasOneDescriptor, BelongsToDescriptor,
                             HasManyDescriptor, HasAndBelongsToManyDescriptor)

from . import BaseTestCase, DbBaseTestCase


class AllTests(DbBaseTestCase):
    def setUp(self):
        super(AllTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_returns_object_set(self):
        assert isinstance(self.Artist.all(), ObjectSet)

    def test_no_objects(self):
        assert len(self.Artist.all()) == 0

    def test_some_objects(self):
        self.Artist.create()
        self.Artist.create()
        assert len(self.Artist.all()) == 2

    def test_some_objects_deleted(self):
        a = self.Artist.create()
        self.Artist.create()
        a.delete()
        assert len(self.Artist.all()) == 1


class CreateTests(DbBaseTestCase):
    def setUp(self):
        super(CreateTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_object_is_saved(self):
        self.Artist.create()
        assert len(self.Artist.all()) == 1

    def test_object_is_returned(self):
        assert isinstance(self.Artist.create(), self.Artist)


class GetTests(DbBaseTestCase):
    def setUp(self):
        super(GetTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_by_id(self):
        a = self.Artist()
        a.save()
        assert self.Artist.get(a['id']).fields.as_dict() == a.fields.as_dict()

    def test_by_kwargs(self):
        a = self.Artist(name='Andrei', country='Romania')
        a.save()
        assert self.Artist.get(name='Andrei', country='Romania').fields.as_dict() == a.fields.as_dict()

    def test_by_id_inexistent(self):
        assert self.Artist.get('id') is None

    def test_by_kwargs_inexistent(self):
        assert self.Artist.get(name='inexistent') is None


class GetOrCreateTests(DbBaseTestCase):
    def setUp(self):
        super(GetOrCreateTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_existent(self):
        a = self.Artist.create()
        assert self.Artist.get_or_create(a['id'])[1] is False

    def test_inexistent(self):
        assert self.Artist.get_or_create(name='Andrei')[1] is True


class FilterTests(DbBaseTestCase):
    def setUp(self):
        super(FilterTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_returns_object_set(self):
        assert isinstance(self.Artist.filter(), ObjectSet)

    def test_by_ids_no_objects(self):
        assert len(self.Artist.filter(['id'])) == 0

    def test_by_kwargs_no_objects(self):
        assert len(self.Artist.filter(id='id')) == 0

    def test_by_ids_some_objects_valid_filter(self):
        a = self.Artist.create()
        self.Artist.create()
        objs = self.Artist.filter([a['id']])
        assert len(objs) == 1
        assert isinstance(objs[0], self.Artist)
        assert objs[0]['id'] == a['id']

    def test_by_kwargs_some_objects_valid_filter(self):
        a = self.Artist.create()
        self.Artist.create()
        objs = self.Artist.filter(id=a['id'])
        assert len(objs) == 1
        assert isinstance(objs[0], self.Artist)
        assert objs[0]['id'] == a['id']

    def test_by_ids_some_objects_deleted_valid_filter(self):
        a = self.Artist.create()
        a_id = a['id']
        self.Artist.create()
        a.delete()
        assert len(self.Artist.filter([a_id])) == 0

    def test_by_kwargs_some_objects_deleted_valid_filter(self):
        a = self.Artist.create()
        a_id = a['id']
        self.Artist.create()
        a.delete()
        assert len(self.Artist.filter(id=a_id)) == 0

    def test_by_ids_some_objects_invalid_filter(self):
        self.Artist.create()
        self.Artist.create()
        assert len(self.Artist.filter(['id'])) == 0

    def test_by_kwargs_some_objects_invalid_filter(self):
        self.Artist.create()
        self.Artist.create()
        assert len(self.Artist.filter(id='id')) == 0


class CountTests(DbBaseTestCase):
    def setUp(self):
        super(CountTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_no_objects(self):
        assert self.Artist.count() == 0

    def test_some_objects(self):
        self.Artist.create()
        self.Artist.create()
        assert self.Artist.count() == 2


class WrapTests(DbBaseTestCase):
    def setUp(self):
        super(WrapTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_correct_model_cls(self):
        obj = self.Artist.objects._wrap({})
        assert isinstance(obj, self.Artist)

    def test_correct_fields(self):
        doc = {'name': 'Andrei'}
        obj = self.Artist.objects._wrap(doc)
        assert obj.fields.__dict__ == doc


class ObjectSetTests(DbBaseTestCase):
    def setUp(self):
        super(ObjectSetTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_cache_set_by_call(self):
        objs = self.Artist.all()
        # Cache should be None; no queries have been run
        assert objs.result_cache is None
        # Run query
        len(objs)
        # Cache should have been populated by run query
        assert objs.result_cache is not None

    def test_same_cache_between_calls(self):
        objs = self.Artist.all()
        len(objs)
        result_cache = objs.result_cache
        # Another call should hit the cache instead of running the query again
        len(objs)
        assert objs.result_cache == result_cache


class LenTests(DbBaseTestCase):
    def setUp(self):
        super(LenTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_no_objects(self):
        assert len(self.Artist.all()) == 0

    def test_some_objects(self):
        self.Artist.create()
        self.Artist.create()
        assert len(self.Artist.all()) == 2

    def test_some_objects_deleted(self):
        a = self.Artist.create()
        self.Artist.create()
        a.delete()
        assert len(self.Artist.all()) == 1


class GetItemTests(DbBaseTestCase):
    def setUp(self):
        super(GetItemTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_no_objects(self):
        with pytest.raises(IndexError):
            self.Artist.all()[0]

    def test_one_object(self):
        a = self.Artist.create()
        assert self.Artist.all()[0]['id'] == a['id']

    def test_some_objects(self):
        a1 = self.Artist.create()
        a2 = self.Artist.create()
        assert self.Artist.all()[0]['id'] in (a1['id'], a2['id'])
        assert self.Artist.all()[1]['id'] in (a1['id'], a2['id'])

    def test_invalid_index(self):
        self.Artist.create()
        with pytest.raises(IndexError):
            self.Artist.all()[1]

    # TODO: Write tests for negative indices, slices


class CustomQueryTests(DbBaseTestCase):
    def setUp(self):
        super(CustomQueryTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_query_correctly_handled(self):
        self.Artist.create(name='John')
        self.Artist.create(name='Andrei')
        with get_conn() as conn:
            # order_by should be correctly handled by self.Artist
            results = list(self.Artist.order_by('name').run(conn))
        assert results[0]['name'] == 'Andrei'
        assert results[1]['name'] == 'John'
