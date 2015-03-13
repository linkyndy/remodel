import rethinkdb as r

from remodel.helpers import create_tables, drop_tables, create_indexes
from remodel.models import Model

from . import BaseTestCase, DbBaseTestCase


class CreateTablesTests(DbBaseTestCase):
    def assert_table_created(self, table):
        assert table in r.table_list().run()

    def test_new_table(self):
        class Artist(Model):
            pass

        create_tables()
        self.assert_table_created('artists')

    def test_existing_table(self):
        class Artist(Model):
            pass

        create_tables()
        create_tables()
        self.assert_table_created('artists')


class DropTablesTests(DbBaseTestCase):
    def setUp(self):
        super(DropTablesTests, self).setUp()

        class Artist(Model):
            pass

        create_tables()

    def assert_table_dropped(self, table):
        assert table not in r.table_list().run()

    def test_existing_table(self):
        drop_tables()
        self.assert_table_dropped('artists')

    def test_dropped_table(self):
        drop_tables()
        drop_tables()
        self.assert_table_dropped('artists')


class CreateIndexesTests(DbBaseTestCase):
    def assert_indexes_created(self, table, indexes):
        assert set(indexes) == set(r.table(table).index_list().run())

    def test_new_index(self):
        class Order(Model):
            belongs_to = ('Customer',)

        create_tables()
        create_indexes()
        self.assert_indexes_created('orders', ['customer_id'])

    def test_existing_index(self):
        class Order(Model):
            belongs_to = ('Customer',)

        create_tables()
        create_indexes()
        create_indexes()
        self.assert_indexes_created('orders', ['customer_id'])
