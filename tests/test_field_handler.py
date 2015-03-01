import pytest
import unittest

from remodel.helpers import create_tables, create_indexes
from remodel.models import Model
from remodel.registry import index_registry
from remodel.related import (HasOneDescriptor, BelongsToDescriptor,
                             HasManyDescriptor, HasAndBelongsToManyDescriptor)

from . import BaseTestCase, DbBaseTestCase


class RelationDeclarationTests(BaseTestCase):
    """
    Tests if relations are correctly declared or not
    """

    def test_valid_relation(self):
        class Artist(Model):
            has_one = ('Bio',)

    def test_invalid_relation(self):
        with pytest.raises(ValueError):
            class Artist(Model):
                has_one = 'Bio'
        with pytest.raises(ValueError):
            class Artist(Model):
                has_one = ['Bio']
        with pytest.raises(ValueError):
            class Artist(Model):
                has_one = list
        with pytest.raises(NameError):
            class Artist(Model):
                has_one = Bio

    def test_empty_relation(self):
        class Artist(Model):
            has_one = ()

    def test_no_relation(self):
        class Artist(Model):
            pass

    def test_multiple_relation(self):
        class Artist(Model):
            has_one = ('Bio', 'Profile')

    def test_same_multiple_relation(self):
        """
        No error should be thrown; instead create a single relation
        """

        class Artist(Model):
            has_one = ('Bio', 'Bio')


class AttributesTests(BaseTestCase):
    """
    Tests whether field handler attributes are correctly set for given model
    w/ and w/o relations
    """

    def test_removed_attributes(self):
        class Artist(Model):
            has_one = ('Bio',)
            belongs_to = ('Person',)
            has_many = ('Song',)
            has_and_belongs_to_many = ('Taste',)

        fhcls = Artist._field_handler_cls
        assert not hasattr(fhcls, 'model')
        assert not hasattr(fhcls, 'has_one')
        assert not hasattr(fhcls, 'belongs_to')
        assert not hasattr(fhcls, 'has_many')
        assert not hasattr(fhcls, 'has_and_belongs_to_many')

    def test_no_relation(self):
        class Artist(Model):
            pass

        fhcls = Artist._field_handler_cls
        assert fhcls.restricted == set()
        assert fhcls.related == set()

    def test_has_one(self):
        class Artist(Model):
            has_one = ('Bio',)

        fhcls = Artist._field_handler_cls
        assert isinstance(fhcls.bio, HasOneDescriptor)
        assert fhcls.restricted == set()
        assert fhcls.related == set(['bio'])

    def test_belongs_to(self):
        class Artist(Model):
            belongs_to = ('Person',)

        fhcls = Artist._field_handler_cls
        assert isinstance(fhcls.person, BelongsToDescriptor)
        assert fhcls.restricted == set(['person_id'])
        assert fhcls.related == set(['person'])

    def test_has_many(self):
        class Artist(Model):
            has_many = ('Song',)

        fhcls = Artist._field_handler_cls
        assert isinstance(fhcls.songs, HasManyDescriptor)
        assert fhcls.restricted == set()
        assert fhcls.related == set(['songs'])

    def test_has_and_belongs_to_many(self):
        class Artist(Model):
            has_and_belongs_to_many = ('Taste',)

        fhcls = Artist._field_handler_cls
        assert isinstance(fhcls.tastes, HasAndBelongsToManyDescriptor)
        assert fhcls.restricted == set()
        assert fhcls.related == set(['tastes'])

    def test_all_relations(self):
        class Artist(Model):
            has_one = ('Bio',)
            belongs_to = ('Person',)
            has_many = ('Song',)
            has_and_belongs_to_many = ('Taste',)

        fhcls = Artist._field_handler_cls
        assert isinstance(fhcls.bio, HasOneDescriptor)
        assert isinstance(fhcls.person, BelongsToDescriptor)
        assert isinstance(fhcls.songs, HasManyDescriptor)
        assert isinstance(fhcls.tastes, HasAndBelongsToManyDescriptor)
        assert fhcls.restricted == set(['person_id'])
        assert fhcls.related == set(['bio', 'person', 'songs', 'tastes'])


class IndexesTests(BaseTestCase):
    """
    Tests whether indexes are set on the correct tables and keys
    """

    def test_has_one(self):
        class Bear(Model):
            has_one = ('FavoriteCub',)

        assert index_registry.get_for_model('Bear') == set()
        assert index_registry.get_for_model('FavoriteCub') == set(['bear_id'])

    def test_belongs_one(self):
        class Bear(Model):
            belongs_to = ('Family',)

        assert index_registry.get_for_model('Bear') == set(['family_id'])
        assert index_registry.get_for_model('Family') == set()

    def test_has_many(self):
        class Bear(Model):
            has_many = ('Cub',)

        assert index_registry.get_for_model('Bear') == set()
        assert index_registry.get_for_model('Cub') == set(['bear_id'])

    def test_has_and_belongs_to_many(self):
        class Bear(Model):
            has_and_belongs_to_many = ('Continent',)

        assert index_registry.get_for_model('Bear') == set()
        assert index_registry.get_for_model('Continent') == set()
        assert index_registry.get_for_model('_BearContinent') == set(['bear_id', 'continent_id'])

    def test_all_relations(self):
        class Bear(Model):
            has_one = ('FavoriteCub',)
            belongs_to = ('Family',)
            has_many = ('Cub',)
            has_and_belongs_to_many = ('Continent',)

        assert index_registry.get_for_model('Bear') == set(['family_id'])
        assert index_registry.get_for_model('FavoriteCub') == set(['bear_id'])
        assert index_registry.get_for_model('Family') == set()
        assert index_registry.get_for_model('Cub') == set(['bear_id'])
        assert index_registry.get_for_model('Continent') == set()
        assert index_registry.get_for_model('_BearContinent') == set(['bear_id', 'continent_id'])

class AttributeAccessTests(BaseTestCase):
    """
    Tests whether access is correctly granted to attributes
    """

    def test_normal_field(self):
        class Artist(Model):
            has_one = ('Bio',)
            belongs_to = ('Person',)

        a = Artist()
        a['name'] = 'Andrei'
        a['name']
        del a['name']

    def test_restricted_field(self):
        class Artist(Model):
            belongs_to = ('Person',)

        a = Artist()
        with pytest.raises(KeyError):
            a['person_id'] = 1
        with pytest.raises(KeyError):
            a['person_id']
        with pytest.raises(KeyError):
            del a['person_id']

    def test_relation_field(self):
        class Artist(Model):
            has_one = ('Bio',)

        class Bio(Model):
            pass

        a = Artist()
        with pytest.raises(ValueError):
            # Fails because instance must be saved before assignment
            a['bio'] = Bio()
        a['bio']
        del a['bio']


class AsDictTests(DbBaseTestCase):
    def setUp(self):
        super(AsDictTests, self).setUp()

        class Artist(Model):
            belongs_to = ('Person',)
        self.Artist = Artist

        class Person(Model):
            pass
        self.Person = Person

        create_tables()
        create_indexes()

    def test_normal_fields(self):
        a = self.Artist(name='Andrei')
        a['country'] = 'Romania'
        assert a.fields.as_dict() == {'name': 'Andrei', 'country': 'Romania'}

    def test_belongs_to(self):
        p = self.Person()
        p.save()
        a = self.Artist(person=p)
        assert a.fields.as_dict() == {'person_id': p['id']}
