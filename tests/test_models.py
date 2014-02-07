import pytest
import rethinkdb as r
import unittest

from remodel.connection import connection_store as cs
from remodel.errors import OperationError
from remodel.models import Model
from remodel.registry import model_registry
from remodel.related import (HasOneDescriptor, BelongsToDescriptor,
                             HasManyDescriptor, HasAndBelongsToManyDescriptor)
from remodel.utils import create_tables, create_indexes

from . import BaseTestCase, DbBaseTestCase


class ModelTests(BaseTestCase):
    def test_model_attributes(self):
        class Artist(Model):
            pass

        assert hasattr(Artist, '_table')
        assert hasattr(Artist, '_connection_store')
        assert hasattr(Artist, 'has_one')
        assert hasattr(Artist, 'has_many')
        assert hasattr(Artist, 'has_and_belongs_to_many')
        assert hasattr(Artist, 'belongs_to')
        assert hasattr(Artist, '_field_handler_cls')


class FieldTests(BaseTestCase):
    """
    Tests both whether fields passed as keyword arguments on a new document
    and fields passed after document creation are correctly set and retrieved
    """

    def setUp(self):
        super(FieldTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

    def test_new_document_with_no_fields(self):
        a = self.Artist()

    def test_new_document_with_one_field(self):
        a = self.Artist(name='Andrei')
        assert 'name' in a
        assert a['name'] == 'Andrei'

    def test_new_document_with_several_fields(self):
        a = self.Artist(name='Andrei', country='Romania', height='tall')
        assert 'name' in a and 'country' in a and 'height' in a
        assert (a['name'] == 'Andrei' and
                a['country'] == 'Romania' and
                a['height'] == 'tall')

    def test_existing_document(self):
        a = self.Artist()
        a['name'] = 'Andrei'
        assert 'name' in a
        assert a['name'] == 'Andrei'


class RelatedFieldTests(DbBaseTestCase):
    """
    Tests both whether related fields passed as keyword arguments on a new document
    and related fields passed after document creation are correctly set and retrieved
    """

    def setUp(self):
        super(RelatedFieldTests, self).setUp()

        class Artist(Model):
            has_one = ('Bio',)
            belongs_to = ('Person',)
            has_many = ('Song',)
            has_and_belongs_to_many = ('Taste',)
        self.Artist = Artist

        class Bio(Model):
            pass
        self.Bio = Bio

        class Person(Model):
            pass
        self.Person = Person

        class Song(Model):
            pass
        self.Song = Song

        class Taste(Model):
            pass
        self.Taste = Taste

        create_tables()
        create_indexes()

    def test_existing_document_with_has_one_field(self):
        a = self.Artist()
        a.save()
        b = self.Bio()
        a['bio'] = b
        assert a['bio'] is b

    def test_new_document_with_belongs_to_field(self):
        p = self.Person()
        p.save()
        a = self.Artist(person=p)
        assert a['person'] is p

    def test_existing_document_with_belongs_to_field(self):
        p = self.Person()
        p.save()
        a = self.Artist()
        a['person'] = p
        assert a['person'] is p

    def test_existing_document_with_has_many_field(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]

    def test_existing_document_with_has_and_belongs_to_many_field(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]


class SaveTests(DbBaseTestCase):
    def setUp(self):
        super(SaveTests, self).setUp()

        class Artist(Model):
            has_one = ('Bio',)
            belongs_to = ('Person',)
        self.Artist = Artist

        class Bio(Model):
            pass
        self.Bio = Bio

        class Person(Model):
            pass
        self.Person = Person

        create_tables()
        create_indexes()

    def assert_saved(self, table, fields):
        assert len(list(r.table(table).filter(fields).run(cs.get()))) == 1

    def test_insert(self):
        a = self.Artist(name='Andrei')
        a.save()
        self.assert_saved(a._table, a.fields.as_dict())

    def test_update(self):
        a = self.Artist(name='Andrei')
        a.save()
        a.save()
        self.assert_saved(a._table, a.fields.as_dict())

    def test_update_with_added_field(self):
        a = self.Artist(name='Andrei')
        a.save()
        a['country'] = 'Romania'
        a.save()
        self.assert_saved(a._table, a.fields.as_dict())

    def test_update_with_removed_field(self):
        a = self.Artist(name='Andrei')
        a.save()
        del a['name']
        a.save()
        self.assert_saved(a._table, a.fields.as_dict())

    def test_belongs_to(self):
        p = self.Person()
        p.save()
        a = self.Artist()
        a['person'] = p
        a.save()
        self.assert_saved(a._table, a.fields.as_dict())

    def test_updated_belongs_to(self):
        p1 = self.Person()
        p1.save()
        a = self.Artist()
        a['person'] = p1
        a.save()
        p2 = self.Person()
        p2.save()
        a['person'] = p2
        a.save()
        self.assert_saved(a._table, a.fields.as_dict())

    def test_removed_belongs_to(self):
        p = self.Person()
        p.save()
        a = self.Artist()
        a['person'] = p
        a.save()
        del a['person']
        a.save()
        self.assert_saved(a._table, a.fields.as_dict())

    def test_has_one(self):
        a = self.Artist()
        a.save()
        b = self.Bio()
        a['bio'] = b
        b.save()
        self.assert_saved(b._table, b.fields.as_dict())

    def test_updated_has_one(self):
        a = self.Artist()
        a.save()
        b1 = self.Bio()
        a['bio'] = b1
        b1.save()
        b2 = self.Bio()
        a['bio'] = b2
        b1.save()
        self.assert_saved(b1._table, b1.fields.as_dict())

    def test_removed_has_one(self):
        a = self.Artist()
        a.save()
        b = self.Bio()
        a['bio'] = b
        b.save()
        del a['bio']
        b.save()
        self.assert_saved(b._table, b.fields.as_dict())


class DeleteTests(DbBaseTestCase):
    def setUp(self):
        super(DeleteTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def assert_deleted(self, table, fields):
        assert len(list(r.table(table).filter(fields).run(cs.get()))) == 0

    def test_not_saved(self):
        a = self.Artist()
        with pytest.raises(OperationError):
            a.delete()

    def test_already_deleted(self):
        a = self.Artist()
        a.save()
        a.delete()
        with pytest.raises(OperationError):
            a.delete()

    # TODO: Add tests for confirming that related objects have no reference left to the deleted object


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


class AllTests(DbBaseTestCase):
    def setUp(self):
        super(AllTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_no_objects(self):
        assert len(list(self.Artist.all())) == 0

    def test_some_objects(self):
        self.Artist.create()
        self.Artist.create()
        assert len(list(self.Artist.all())) == 2

    def test_some_objects_deleted(self):
        a = self.Artist.create()
        self.Artist.create()
        a.delete()
        assert len(list(self.Artist.all())) == 1


class FilterTests(DbBaseTestCase):
    def setUp(self):
        super(FilterTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def test_no_objects(self):
        assert len(list(self.Artist.filter(id='id'))) == 0

    def test_some_objects_valid_filter(self):
        a = self.Artist.create()
        self.Artist.create()
        assert len(list(self.Artist.filter(id=a['id']))) == 1

    def test_some_objects_deleted_valid_filter(self):
        a = self.Artist.create()
        a_id = a['id']
        self.Artist.create()
        a.delete()
        assert len(list(self.Artist.filter(id=a_id))) == 0

    def test_some_objects_invalid_filter(self):
        self.Artist.create()
        self.Artist.create()
        assert len(list(self.Artist.filter(id='id'))) == 0
