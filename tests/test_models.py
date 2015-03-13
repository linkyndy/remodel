import pytest
import rethinkdb as r

from remodel.errors import OperationError
from remodel.helpers import create_tables, create_indexes
from remodel.models import Model, before_save, after_save, before_delete, after_delete, after_init
from remodel.object_handler import ObjectHandler
from remodel.registry import model_registry
from remodel.related import (HasOneDescriptor, BelongsToDescriptor,
                             HasManyDescriptor, HasAndBelongsToManyDescriptor)

from . import BaseTestCase, DbBaseTestCase


class ModelTests(BaseTestCase):
    def test_model_attributes(self):
        class Artist(Model):
            pass

        assert hasattr(Artist, '_table')
        assert hasattr(Artist, 'has_one')
        assert hasattr(Artist, 'has_many')
        assert hasattr(Artist, 'has_and_belongs_to_many')
        assert hasattr(Artist, 'belongs_to')
        assert hasattr(Artist, '_field_handler_cls')
        assert hasattr(Artist, 'object_handler')
        assert hasattr(Artist, '_callbacks')
        assert hasattr(Artist, 'objects')

    def test_default_object_handler_cls(self):
        class Artist(Model):
            pass

        assert Artist.object_handler == ObjectHandler
        assert isinstance(Artist.objects, ObjectHandler)

    def test_custom_object_handler_cls(self):
        class CustomObjectHandler(ObjectHandler):
            pass

        class Artist(Model):
            object_handler = CustomObjectHandler

        assert Artist.object_handler == CustomObjectHandler
        assert isinstance(Artist.objects, CustomObjectHandler)

    def test_callback_keys(self):
        """
        Test whether all callback keys are created for model callback registry
        """

        class Artist(Model):
            pass

        assert isinstance(Artist._callbacks, dict)
        assert 'before_save' in Artist._callbacks
        assert 'after_save' in Artist._callbacks
        assert 'before_delete' in Artist._callbacks
        assert 'after_delete' in Artist._callbacks
        assert 'after_init' in Artist._callbacks

    def test_callback_named_methods_registered(self):
        """
        Test whether all callback named methods are registered to the model
        callback registry
        """

        class Artist(Model):
            def before_save(self):
                pass

            def after_save(self):
                pass

            def before_delete(self):
                pass

            def after_delete(self):
                pass

            def after_init(self):
                pass

        assert 'before_save' in Artist._callbacks['before_save']
        assert 'after_save' in Artist._callbacks['after_save']
        assert 'before_delete' in Artist._callbacks['before_delete']
        assert 'after_delete' in Artist._callbacks['after_delete']
        assert 'after_init' in Artist._callbacks['after_init']

    def test_callback_decorated_methods_registered(self):
        """
        Test whether all callback decorated methods are registered to the model
        callback registry
        """

        class Artist(Model):
            @before_save
            def bef_save(self):
                pass

            @after_save
            def aft_save(self):
                pass

            @before_delete
            def bef_delete(self):
                pass

            @after_delete
            def aft_delete(self):
                pass

            @after_init
            def aft_init(self):
                pass

        assert 'bef_save' in Artist._callbacks['before_save']
        assert 'aft_save' in Artist._callbacks['after_save']
        assert 'bef_delete' in Artist._callbacks['before_delete']
        assert 'aft_delete' in Artist._callbacks['after_delete']
        assert 'aft_init' in Artist._callbacks['after_init']


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
        assert len(list(r.table(table).filter(fields).run())) == 1

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
        assert len(list(r.table(table).filter(fields).run())) == 0

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


class GetTests(BaseTestCase):
    def setUp(self):
        super(GetTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

    def test_existing_field(self):
        a = self.Artist(name='Andrei')
        assert a.get('name') == 'Andrei'

    def test_inexisting_field_with_default(self):
        a = self.Artist()
        assert a.get('name', 'Andrei') == 'Andrei'

    def test_inexisting_field_without_default(self):
        a = self.Artist()
        assert a.get('name') is None


class UpdateTests(DbBaseTestCase):
    def setUp(self):
        super(UpdateTests, self).setUp()

        class Artist(Model):
            pass
        self.Artist = Artist

        create_tables()
        create_indexes()

    def assert_updated(self, table, fields):
        assert len(list(r.table(table).filter(fields).run())) == 1

    def test_one_field_updated(self):
        a = self.Artist()
        a.update(name='Andrei')
        assert 'name' in a
        assert a['name'] == 'Andrei'

    def test_several_fields_updated(self):
        a = self.Artist()
        a.update(name='Andrei', country='Romania', height='tall')
        assert 'name' in a and 'country' in a and 'height' in a
        assert (a['name'] == 'Andrei' and
                a['country'] == 'Romania' and
                a['height'] == 'tall')

    def test_new_document_with_no_fields(self):
        a = self.Artist(name='Andrei')
        a.update()
        self.assert_updated(a._table, a.fields.as_dict())

    def test_new_document_with_one_field(self):
        a = self.Artist(name='Andrei')
        a.update(country='Romania')
        self.assert_updated(a._table, a.fields.as_dict())

    def test_new_document_with_several_fields(self):
        a = self.Artist(name='Andrei')
        a.update(country='Romania', city='Timisoara', male=True)
        self.assert_updated(a._table, a.fields.as_dict())

    def test_existing_document_with_no_fields(self):
        a = self.Artist.create(name='Andrei')
        a.update()
        self.assert_updated(a._table, a.fields.as_dict())

    def test_existing_document_with_one_field(self):
        a = self.Artist.create(name='Andrei')
        a.update(country='Romania')
        self.assert_updated(a._table, a.fields.as_dict())

    def test_existing_document_with_several_fields(self):
        a = self.Artist.create(name='Andrei')
        a.update(country='Romania', city='Timisoara', male=True)
        self.assert_updated(a._table, a.fields.as_dict())


class CallbackTests(DbBaseTestCase):
    """
    Tests whether callbacks are run and also that they are run at the desired
    moment
    """

    # TODO: Make these tests more relevant by using mocks

    def assert_saved(self, table, fields):
        assert len(list(r.table(table).filter(fields).run())) == 1

    def assert_not_saved(self, table, fields):
        assert len(list(r.table(table).filter(fields).run())) == 0

    def assert_deleted(self, table, fields):
        assert len(list(r.table(table).filter(fields).run())) == 0

    def test_before_save(self):
        class Artist(Model):
            def before_save(self):
                self['verified'] = True

        create_tables()

        a = Artist()
        a.save()
        assert a['verified'] is True
        self.assert_saved(a._table, a.fields.as_dict())

    def test_after_save(self):
        class Artist(Model):
            def after_save(self):
                self['confirmed'] = False

        create_tables()

        a = Artist()
        a.save()
        assert a['confirmed'] is False
        self.assert_not_saved(a._table, a.fields.as_dict())

    def test_before_delete(self):
        class Artist(Model):
            def before_delete(self):
                self['deleted'] = True

        create_tables()

        a = Artist.create()
        a.delete()
        assert a['deleted'] is True
        self.assert_deleted(a._table, a.fields.as_dict())

    def test_after_delete(self):
        class Artist(Model):
            def after_delete(self):
                self['deleted'] = True

        create_tables()

        a = Artist.create()
        a.delete()
        assert a['deleted'] is True
        self.assert_deleted(a._table, a.fields.as_dict())

    def test_after_init(self):
        class Artist(Model):
            def after_init(self):
                self['new'] = True

        a = Artist()
        assert a['new'] is True
