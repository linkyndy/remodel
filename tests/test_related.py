import pytest

from remodel.connection import get_conn
from remodel.helpers import create_tables, create_indexes
from remodel.models import Model
from remodel.related import (HasOneDescriptor, BelongsToDescriptor,
                             HasManyDescriptor, HasAndBelongsToManyDescriptor)

from . import BaseTestCase, DbBaseTestCase

# TODO: Ensure models are saved/retrieved correctly by performing direct queries


class HasOneDescriptorTests(DbBaseTestCase):
    """
    Tests whether HasOneDescriptor correctly responds to get/set/delete actions
    in various cases
    """

    def setUp(self):
        super(HasOneDescriptorTests, self).setUp()

        class Artist(Model):
            has_one = ('Bio',)
        self.Artist = Artist

        class Bio(Model):
            pass
        self.Bio = Bio

        create_tables()
        create_indexes()

    def test_get_for_unsaved_object(self):
        a = self.Artist()
        assert a['bio'] is None
        assert a.fields._bio_cache is None

    def test_get_for_saved_object(self):
        a = self.Artist()
        a.save()
        with pytest.raises(AttributeError):
            # Cache not set by this point
            a.fields._bio_cache
        assert a['bio'] is None
        assert a.fields._bio_cache is None

    def test_get_cached(self):
        a = self.Artist()
        a.save()
        a['bio']
        # Cache set by this point
        assert a.fields._bio_cache is None
        # TODO: Test the cache was actually hit
        assert a['bio'] is None

    def test_get_cache_changed(self):
        a = self.Artist()
        a.save()
        a['bio']
        # Cache set by this point
        b = self.Bio()
        a['bio'] = b
        # Cache changed by this point
        assert a.fields._bio_cache is b
        # TODO: Test the cache was actually hit
        assert a['bio'] is b

    def test_set_invalid_instance(self):
        a = self.Artist()
        with pytest.raises(ValueError):
            a['bio'] = self.Artist()

    def test_set_none_uncached(self):
        a = self.Artist()
        a['bio'] = None
        assert a.fields._bio_cache is None

    def test_set_none_cached_with_none(self):
        a = self.Artist()
        a['bio'] = None
        # Cache set by this point
        a['bio'] = None
        assert a.fields._bio_cache is None

    def test_set_none_cached(self):
        a = self.Artist()
        a.save()
        b = self.Bio()
        a['bio'] = b
        # Cache set by this point
        a['bio'] = None
        assert 'artist_id' not in b.fields.__dict__
        assert a.fields._bio_cache is None

    def test_set_for_unsaved_object(self):
        a = self.Artist()
        b = self.Bio()
        with pytest.raises(ValueError):
            a['bio'] = b

    def test_set_valid(self):
        a = self.Artist()
        a.save()
        b = self.Bio()
        a['bio'] = b
        assert b.fields.__dict__['artist_id'] == a['id']
        assert a.fields._bio_cache is b


class BelongsToDescriptorTests(DbBaseTestCase):
    """
    Tests whether BelongsToDescriptor correctly responds to get/set/delete actions
    in various cases
    """

    def setUp(self):
        super(BelongsToDescriptorTests, self).setUp()

        class Artist(Model):
            belongs_to = ('Person',)
        self.Artist = Artist

        class Person(Model):
            pass
        self.Person = Person

        create_tables()
        create_indexes()

    def test_get_for_saved_object(self):
        a = self.Artist()
        assert a['person'] is None
        assert a.fields._person_cache is None

    def test_get_for_unsaved_object(self):
        a = self.Artist()
        a.save()
        with pytest.raises(AttributeError):
            # Cache not set by this point
            a.fields._person_cache
        assert a['person'] is None
        assert a.fields._person_cache is None

    def test_get_cached(self):
        a = self.Artist()
        a.save()
        a['person']
        # Cache set by this point
        assert a.fields._person_cache is None
        # TODO: Test the cache was actually hit
        assert a['person'] is None

    def test_get_cache_changed(self):
        a = self.Artist()
        a.save()
        a['person']
        # Cache set by this point
        p = self.Person()
        p.save()
        a['person'] = p
        # Cache changed by this point
        assert a.fields._person_cache is p
        # TODO: Test the cache was actually hit
        assert a['person'] is p

    def test_set_invalid_instance(self):
        a = self.Artist()
        with pytest.raises(ValueError):
            a['person'] = self.Artist()

    def test_set_none_with_inexistent_value(self):
        a = self.Artist()
        a['person'] = None
        assert a.fields._person_cache is None

    def test_set_none_with_existent_value(self):
        a = self.Artist()
        p = self.Person()
        p.save()
        a['person'] = p
        # Cache set by this point
        a['person'] = None
        assert 'person_id' not in a.fields.__dict__
        assert a.fields._person_cache is None

    def test_set_unsaved_object(self):
        a = self.Artist()
        p = self.Person()
        with pytest.raises(ValueError):
            a['person'] = p

    def test_set_valid(self):
        a = self.Artist()
        p = self.Person()
        p.save()
        a['person'] = p
        assert a.fields.__dict__['person_id'] == p['id']
        assert a.fields._person_cache is p


class HasManyDescriptorTests(DbBaseTestCase):
    """
    Tests whether HasManyDescriptor correctly responds to get/set/delete actions
    in various cases
    """

    def setUp(self):
        super(HasManyDescriptorTests, self).setUp()

        class Artist(Model):
            has_many = ('Song',)
        self.Artist = Artist

        class Song(Model):
            pass
        self.Song = Song

        create_tables()
        create_indexes()

    def test_get_uncached(self):
        a = self.Artist()
        a.save()
        rel_object_handler = a['songs']
        rel_object_handler_cls = a._field_handler_cls.songs.related_object_handler_cls
        assert isinstance(rel_object_handler, rel_object_handler_cls)
        assert a.fields._songs_cache is rel_object_handler

    def test_get_cached(self):
        a = self.Artist()
        a.save()
        rel_object_handler = a['songs']
        rel_object_handler_cls = a._field_handler_cls.songs.related_object_handler_cls
        # Cache set by this point
        assert isinstance(rel_object_handler, rel_object_handler_cls)
        assert a.fields._songs_cache is rel_object_handler
        # TODO: Test the cache was actually hit
        assert a['songs'] is rel_object_handler

    def test_set(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        rel_object_handler_all = a['songs'].all()
        assert len(rel_object_handler_all) == 2
        assert rel_object_handler_all[0]['id'] in [s1['id'], s2['id']]
        assert rel_object_handler_all[1]['id'] in [s1['id'], s2['id']]

    def test_set_with_existent_objects(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        s3 = self.Song()
        a['songs'] = [s1, s2]
        # Songs set by this point
        a['songs'] = [s3]
        rel_object_handler_all = a['songs'].all()
        assert len(rel_object_handler_all) == 1
        assert rel_object_handler_all[0]['id'] == s3['id']

    def test_set_with_invalid_objects(self):
        a = self.Artist()
        a.save()
        s = self.Song()
        with pytest.raises(TypeError):
            a['songs'] = s

    def test_delete(self):
        a = self.Artist()
        a.save()
        del a['songs']
        rel_object_handler_all = a['songs'].all()
        assert len(rel_object_handler_all) == 0

    def test_delete_with_existent_objects(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        # Songs set by this point
        del a['songs']
        rel_object_handler_all = a['songs'].all()
        assert len(rel_object_handler_all) == 0


class RelatedSetTests(DbBaseTestCase):
    """
    Tests whether RelatedSet correctly responds to its defined interface
    in various cases
    """

    def setUp(self):
        super(RelatedSetTests, self).setUp()

        class Artist(Model):
            has_many = ('Song',)
        self.Artist = Artist

        class Song(Model):
            pass
        self.Song = Song

        create_tables()
        create_indexes()

    def test_all_nothing_set(self):
        a = self.Artist()
        a.save()
        assert len(a['songs'].all()) == 0

    def test_all_objects_set(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        objs = a['songs'].all()
        assert len(objs) == 2
        assert objs[0]['id'] in [s1['id'], s2['id']]
        assert objs[1]['id'] in [s1['id'], s2['id']]

    def test_all_objects_deleted(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        a['songs'].remove(s1)
        objs = a['songs'].all()
        assert len(objs) == 1
        assert objs[0]['id'] == s2['id']

    def test_filter_by_ids_nothing_set(self):
        a = self.Artist()
        a.save()
        assert len(a['songs'].filter(['id'])) == 0

    def test_filter_by_kwargs_nothing_set(self):
        a = self.Artist()
        a.save()
        assert len(a['songs'].filter(id='id')) == 0

    def test_filter_by_ids_objects_set_valid_filter(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        objs = a['songs'].filter([s1['id']])
        assert len(objs) == 1
        assert objs[0]['id'] == s1['id']

    def test_filter_by_kwargs_objects_set_valid_filter(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        objs = a['songs'].filter(id=s1['id'])
        assert len(objs) == 1
        assert objs[0]['id'] == s1['id']

    def test_filter_by_ids_objects_deleted_valid_filter(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        a['songs'].remove(s1)
        objs = a['songs'].filter([s1['id']])
        assert len(objs) == 0

    def test_filter_by_kwargs_objects_deleted_valid_filter(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        a['songs'].remove(s1)
        objs = a['songs'].filter(id=s1['id'])
        assert len(objs) == 0

    def test_filter_by_ids_objects_set_invalid_filter(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        objs = a['songs'].filter(['id'])
        assert len(objs) == 0

    def test_filter_by_kwargs_objects_set_invalid_filter(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        objs = a['songs'].filter(id='id')
        assert len(objs) == 0

    def test_get_by_id(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        obj = a['songs'].get(s1['id'])
        assert obj.fields.as_dict() == s1.fields.as_dict()

    def test_get_by_kwargs(self):
        a = self.Artist()
        a.save()
        s1 = self.Song(name='My Song')
        s2 = self.Song()
        a['songs'] = [s1, s2]
        obj = a['songs'].get(name='My Song')
        assert obj.fields.as_dict() == s1.fields.as_dict()

    def test_get_by_id_inexistent(self):
        a = self.Artist()
        a.save()
        assert a['songs'].get('id') is None

    def test_get_by_kwargs_inexistent(self):
        a = self.Artist()
        a.save()
        assert a['songs'].get(name='inexistent') is None

    def test_create_object_is_saved(self):
        a = self.Artist()
        a.save()
        a['songs'].create()
        assert len(a['songs'].all()) == 1

    def test_create_object_is_returned(self):
        a = self.Artist()
        a.save()
        assert isinstance(a['songs'].create(), self.Song)

    def test_get_or_create_existent(self):
        a = self.Artist()
        a.save()
        s = a['songs'].create()
        assert a['songs'].get_or_create(s['id'])[1] is False

    def test_get_or_create_inexistent(self):
        a = self.Artist()
        a.save()
        assert a['songs'].get_or_create(name='My Song')[1] is True

    def test_count_no_objects(self):
        a = self.Artist()
        a.save()
        assert a['songs'].count() == 0

    def test_count_some_objects(self):
        a = self.Artist()
        a.save()
        a['songs'].create()
        a['songs'].create()
        assert a['songs'].count() == 2

    def test_add_with_invalid_object(self):
        a = self.Artist()
        a.save()
        with pytest.raises(TypeError):
            a['songs'].add(self.Artist())

    def test_add_with_single_object(self):
        a = self.Artist()
        a.save()
        s = self.Song()
        a['songs'].add(s)
        assert s.fields.__dict__['artist_id'] == a['id']
        assert len(a['songs'].all()) == 1

    def test_add_with_multiple_objects(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        s3 = self.Song()
        a['songs'].add(s1, s2, s3)
        assert s1.fields.__dict__['artist_id'] == a['id']
        assert s2.fields.__dict__['artist_id'] == a['id']
        assert s3.fields.__dict__['artist_id'] == a['id']
        assert len(a['songs'].all()) == 3

    def test_add_added_object(self):
        a = self.Artist()
        a.save()
        s = self.Song()
        a['songs'].add(s)
        a['songs'].add(s)
        assert s.fields.__dict__['artist_id'] == a['id']
        assert len(a['songs'].all()) == 1

    def test_remove_with_invalid_object(self):
        a = self.Artist()
        a.save()
        with pytest.raises(ValueError):
            a['songs'].remove(self.Song())

    def test_remove_with_single_object(self):
        a = self.Artist()
        a.save()
        s = self.Song()
        a['songs'] = [s]
        a['songs'].remove(s)
        assert 'artist_id' not in s.fields.__dict__
        assert len(a['songs'].all()) == 0

    def test_remove_with_multiple_objects(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        s3 = self.Song()
        a['songs'] = [s1, s2, s3]
        a['songs'].remove(s1, s2, s3)
        assert 'artist_id' not in s1.fields.__dict__
        assert 'artist_id' not in s2.fields.__dict__
        assert 'artist_id' not in s3.fields.__dict__
        assert len(a['songs'].all()) == 0

    def test_remove_removed_object(self):
        a = self.Artist()
        a.save()
        s = self.Song()
        a['songs'] = [s]
        a['songs'].remove(s)
        with pytest.raises(ValueError):
            a['songs'].remove(s)

    def test_clear_nothing_set(self):
        a = self.Artist()
        a.save()
        a['songs'].clear()
        assert len(a['songs'].all()) == 0

    def test_clear_objects_set(self):
        a = self.Artist()
        a.save()
        s1 = self.Song()
        s2 = self.Song()
        a['songs'] = [s1, s2]
        a['songs'].clear()
        assert 'artist_id' not in self.Song.get(s1['id']).fields.__dict__
        assert 'artist_id' not in self.Song.get(s2['id']).fields.__dict__
        assert len(a['songs'].all()) == 0

    def test_custom_query_correctly_handled(self):
        a = self.Artist()
        a.save()
        a['songs'].create(name='Sandstorm')
        a['songs'].create(name='Rocket')
        with get_conn() as conn:
            # order_by should be correctly handled by a['songs']
            results = list(a['songs'].order_by('name').run(conn))
        assert results[0]['name'] == 'Rocket'
        assert results[1]['name'] == 'Sandstorm'


class HasAndBelongsToManyDescriptorTests(DbBaseTestCase):
    """
    Tests whether HasAndBelongsToManyDescriptor correctly responds to get/set/delete actions
    in various cases
    """

    def setUp(self):
        super(HasAndBelongsToManyDescriptorTests, self).setUp()

        class Artist(Model):
            has_and_belongs_to_many = ('Taste',)
        self.Artist = Artist

        class Taste(Model):
            pass
        self.Taste = Taste

        create_tables()
        create_indexes()

    def test_get_uncached(self):
        a = self.Artist()
        a.save()
        rel_m2m_object_handler = a['tastes']
        rel_m2m_object_handler_cls = a._field_handler_cls.tastes.related_m2m_object_handler_cls
        assert isinstance(rel_m2m_object_handler, rel_m2m_object_handler_cls)
        assert a.fields._tastes_cache is rel_m2m_object_handler

    def test_get_cached(self):
        a = self.Artist()
        a.save()
        rel_m2m_object_handler = a['tastes']
        rel_m2m_object_handler_cls = a._field_handler_cls.tastes.related_m2m_object_handler_cls
        # Cache set by this point
        assert isinstance(rel_m2m_object_handler, rel_m2m_object_handler_cls)
        assert a.fields._tastes_cache is rel_m2m_object_handler
        # TODO: Test the cache was actually hit
        assert a['tastes'] is rel_m2m_object_handler

    def test_set(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        rel_m2m_object_handler_all = a['tastes'].all()
        assert len(rel_m2m_object_handler_all) == 2
        assert rel_m2m_object_handler_all[0]['id'] in [t1['id'], t2['id']]
        assert rel_m2m_object_handler_all[1]['id'] in [t1['id'], t2['id']]

    def test_set_with_existent_objects(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        t3 = self.Taste()
        t3.save()
        a['tastes'] = [t1, t2]
        # Songs set by this point
        a['tastes'] = [t3]
        rel_m2m_object_handler_all = a['tastes'].all()
        assert len(rel_m2m_object_handler_all) == 1
        assert rel_m2m_object_handler_all[0]['id'] == t3['id']

    def test_set_with_invalid_objects(self):
        a = self.Artist()
        a.save()
        t = self.Taste()
        with pytest.raises(TypeError):
            a['tastes'] = t

    def test_delete(self):
        a = self.Artist()
        a.save()
        del a['tastes']
        rel_m2m_object_handler_all = a['tastes'].all()
        assert len(rel_m2m_object_handler_all) == 0

    def test_delete_with_existent_objects(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        # Songs set by this point
        del a['tastes']
        rel_m2m_object_handler_all = a['tastes'].all()
        assert len(rel_m2m_object_handler_all) == 0


class RelatedM2MSetTests(DbBaseTestCase):
    """
    Tests whether RelatedM2MSet correctly responds to its defined interface
    in various cases
    """

    def setUp(self):
        super(RelatedM2MSetTests, self).setUp()

        class Artist(Model):
            has_and_belongs_to_many = ('Taste',)
        self.Artist = Artist

        class Taste(Model):
            pass
        self.Taste = Taste

        create_tables()
        create_indexes()

    def test_all_nothing_set(self):
        a = self.Artist()
        a.save()
        assert len(a['tastes'].all()) == 0

    def test_all_objects_set(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        objs = a['tastes'].all()
        assert len(objs) == 2
        assert objs[0]['id'] in [t1['id'], t2['id']]
        assert objs[1]['id'] in [t1['id'], t2['id']]

    def test_all_objects_deleted(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        a['tastes'].remove(t1)
        objs = a['tastes'].all()
        assert len(objs) == 1
        assert objs[0]['id'] == t2['id']

    def test_filter_by_ids_nothing_set(self):
        a = self.Artist()
        a.save()
        assert len(a['tastes'].filter(['id'])) == 0

    def test_filter_by_kwargs_nothing_set(self):
        a = self.Artist()
        a.save()
        assert len(a['tastes'].filter(id='id')) == 0

    def test_filter_by_ids_objects_set_valid_filter(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        objs = a['tastes'].filter([t1['id']])
        assert len(objs) == 1
        assert objs[0]['id'] == t1['id']

    def test_filter_by_kwargs_objects_set_valid_filter(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        objs = a['tastes'].filter(id=t1['id'])
        assert len(objs) == 1
        assert objs[0]['id'] == t1['id']

    def test_filter_by_ids_objects_deleted_valid_filter(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        a['tastes'].remove(t1)
        objs = a['tastes'].filter([t1['id']])
        assert len(objs) == 0

    def test_filter_by_kwargs_objects_deleted_valid_filter(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        a['tastes'].remove(t1)
        objs = a['tastes'].filter(id=t1['id'])
        assert len(objs) == 0

    def test_filter_by_ids_objects_set_invalid_filter(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        objs = a['tastes'].filter(['id'])
        assert len(objs) == 0

    def test_filter_by_kwargs_objects_set_invalid_filter(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        objs = a['tastes'].filter(id='id')
        assert len(objs) == 0

    def test_get_by_id(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        obj = a['tastes'].get(t1['id'])
        assert obj.fields.as_dict() == t1.fields.as_dict()

    def test_get_by_kwargs(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste(name='My Taste')
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        obj = a['tastes'].get(name='My Taste')
        assert obj.fields.as_dict() == t1.fields.as_dict()

    def test_get_by_id_inexistent(self):
        a = self.Artist()
        a.save()
        assert a['tastes'].get('id') is None

    def test_get_by_kwargs_inexistent(self):
        a = self.Artist()
        a.save()
        assert a['tastes'].get(name='inexistent') is None

    def test_create_object_is_saved(self):
        a = self.Artist()
        a.save()
        a['tastes'].create()
        assert len(a['tastes'].all()) == 1

    def test_create_object_is_returned(self):
        a = self.Artist()
        a.save()
        assert isinstance(a['tastes'].create(), self.Taste)

    def test_get_or_create_existent(self):
        a = self.Artist()
        a.save()
        t = a['tastes'].create()
        assert a['tastes'].get_or_create(t['id'])[1] is False

    def test_get_or_create_inexistent(self):
        a = self.Artist()
        a.save()
        assert a['tastes'].get_or_create(name='My Taste')[1] is True

    def test_count_no_objects(self):
        a = self.Artist()
        a.save()
        assert a['tastes'].count() == 0

    def test_count_some_objects(self):
        a = self.Artist()
        a.save()
        a['tastes'].create()
        a['tastes'].create()
        assert a['tastes'].count() == 2

    def test_add_with_invalid_object(self):
        a = self.Artist()
        a.save()
        with pytest.raises(TypeError):
            a['tastes'].add(self.Artist())

    def test_add_with_unsaved_object(self):
        a = self.Artist()
        a.save()
        with pytest.raises(ValueError):
            a['tastes'].add(self.Taste())

    def test_add_with_single_object(self):
        a = self.Artist()
        a.save()
        t = self.Taste()
        t.save()
        a['tastes'].add(t)
        assert len(a['tastes'].all()) == 1

    def test_add_with_multiple_objects(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        t3 = self.Taste()
        t3.save()
        a['tastes'].add(t1, t2, t3)
        assert len(a['tastes'].all()) == 3

    def test_add_added_object(self):
        a = self.Artist()
        a.save()
        t = self.Taste()
        t.save()
        a['tastes'].add(t)
        a['tastes'].add(t)
        assert len(a['tastes'].all()) == 1

    def test_remove_with_invalid_object(self):
        a = self.Artist()
        a.save()
        with pytest.raises(TypeError):
            a['tastes'].remove(self.Artist())

    def test_remove_with_single_object(self):
        a = self.Artist()
        a.save()
        t = self.Taste()
        t.save()
        a['tastes'] = [t]
        a['tastes'].remove(t)
        assert len(a['tastes'].all()) == 0

    def test_remove_with_multiple_objects(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        t3 = self.Taste()
        t3.save()
        a['tastes'] = [t1, t2, t3]
        a['tastes'].remove(t1, t2, t3)
        assert len(a['tastes'].all()) == 0

    def test_remove_removed_object(self):
        a = self.Artist()
        a.save()
        t = self.Taste()
        t.save()
        a['tastes'] = [t]
        a['tastes'].remove(t)
        a['tastes'].remove(t)
        assert len(a['tastes'].all()) == 0

    def test_clear_nothing_set(self):
        a = self.Artist()
        a.save()
        a['tastes'].clear()
        assert len(a['tastes'].all()) == 0

    def test_clear_objects_set(self):
        a = self.Artist()
        a.save()
        t1 = self.Taste()
        t1.save()
        t2 = self.Taste()
        t2.save()
        a['tastes'] = [t1, t2]
        a['tastes'].clear()
        assert len(a['tastes'].all()) == 0

    def test_custom_query_correctly_handled(self):
        a = self.Artist()
        a.save()
        a['tastes'].create(name='House')
        a['tastes'].create(name='Classical')
        with get_conn() as conn:
            # order_by should be correctly handled by a['tastes']
            results = list(a['tastes'].order_by('name').run(conn))
        assert results[0]['name'] == 'Classical'
        assert results[1]['name'] == 'House'
