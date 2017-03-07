from rethinkdb import r
from contextlib import contextmanager
try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty


from .utils import Counter


class Connection(object):
    def __init__(self, db='test', host='localhost', port=28015, auth_key='',
                 user='admin', password=''):
        self.db = db
        self.host = host
        self.port = port
        self.auth_key = auth_key
        self.user = user
        self.password = password
        self._conn = None

    def connect(self):
        if rethinkdb.__version__ >= '2.3.0':
            password = self.password if self.password != '' else self.auth_key
            self._conn = rethinkdb.connect(host=self.host, port=self.port,
                                           user=self.user, password=password,
                                           db=self.db)
        else:
            auth_key = self.auth_key if self.auth_key != '' else self.password
            self._conn = rethinkdb.connect(host=self.host, port=self.port,
                                           auth_key=auth_key, db=self.db)

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    @property
    def conn(self):
        if not self._conn:
            self.connect()
        return self._conn


class ConnectionPool(object):
    def __init__(self, max_connections=5):
        self.q = Queue()
        self.max_connections = max_connections
        self._created_connections = Counter()
        self.connection_class = Connection
        self.connection_kwargs = {}

    def configure(self, max_connections=5, **connection_kwargs):
        self.max_connections = max_connections
        self.connection_kwargs = connection_kwargs

    def get(self):
        try:
            return self.q.get_nowait()
        except Empty:
            if self._created_connections.current() < self.max_connections:
                conn = self.connection_class(**self.connection_kwargs).conn
                self._created_connections.incr()
                return conn
            raise

    def put(self, connection):
        self.q.put(connection)
        self._created_connections.decr()

    def created(self):
        return self._created_connections.current()


pool = ConnectionPool()


@contextmanager
def get_conn():
    conn = pool.get()
    try:
        yield conn
    finally:
        pool.put(conn)
