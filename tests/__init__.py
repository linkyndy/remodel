import os
import rethinkdb as r
from rethinkdb.errors import RqlDriverError
import unittest

from remodel.connection import pool, get_conn
from remodel.helpers import create_tables
from remodel.models import Model
from remodel.registry import model_registry, index_registry


def get_env_settings():
    settings = {}
    settings['host'] = os.environ.get('RETHINKDB_HOST', None)
    settings['port'] = os.environ.get('RETHINKDB_PORT', None)
    settings['auth_key'] = os.environ.get('RETHINKDB_AUTH_KEY', None)
    settings['db'] = os.environ.get('RETHINKDB_DB', None)
    return {k: v for k, v in settings.items() if v is not None}


pool.configure(max_connections=1, **get_env_settings())


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        model_registry.clear()
        index_registry.clear()


class DbBaseTestCase(BaseTestCase):
    def setUp(self):
        super(DbBaseTestCase, self).setUp()

        # Create new database and switch to it
        try:
            with get_conn() as conn:
                r.db_create('testing').run(conn)
                conn.use('testing')
        except RqlDriverError:
            raise unittest.SkipTest('RethinkDB is unaccessible')

    def tearDown(self):
        super(DbBaseTestCase, self).tearDown()

        # Drop test database
        with get_conn() as conn:
            r.db_drop('testing').run(conn)
