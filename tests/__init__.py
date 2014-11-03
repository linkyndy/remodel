import rethinkdb as r
from rethinkdb.errors import RqlDriverError
import unittest

from remodel.connection import Connection, connection_store as cs
from remodel.models import Model
from remodel.registry import model_registry, index_registry
from remodel.utils import create_tables


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        model_registry.clear()
        index_registry.clear()


class DbBaseTestCase(BaseTestCase):
    @classmethod
    def setUpClass(cls):
        # Create new connection and add it to the connection store so it can
        # be used by models
        connection = Connection()
        cs.put(connection)

    @classmethod
    def tearDownClass(cls):
        # Remove the connection from the connection store
        cs.remove()

    def setUp(self):
        super(DbBaseTestCase, self).setUp()

        # Create new database and switch to it
        try:
            r.db_create('testing').run(cs.get())
            cs.get().use('testing')
        except RqlDriverError:
            raise unittest.SkipTest('RethinkDB is unaccessible')

    def tearDown(self):
        super(DbBaseTestCase, self).tearDown()

        # Drop test database
        r.db_drop('testing').run(cs.get())




