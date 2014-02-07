import rethinkdb as r


class ConnectionStore(object):
    """
    Basic connection store, allowing only one connection to be stored.
    """

    def __init__(self):
        self.stored = None

    def get(self):
        if not self.stored:
            raise Exception('No connection in store')
        return self.stored.connection

    def put(self, connection):
        self.stored = connection

    def remove(self):
        if not self.stored:
            raise Exception('No connection in store')
        self.stored.close()
        self.stored = None


# Used in ModelBase metaclass to assign a connection store for each Model
# class. Every connection used by models will be picked up from this store.
connection_store = ConnectionStore()


class Connection(object):

    def __init__(self, db='test', host='localhost', port='28015', auth_key=''):
        self.db = db
        self.host = host
        self.port = port
        self.auth_key = auth_key
        self._connection = None

    def connect(self):
        self._connection = r.connect(host=self.host, port=self.port, auth_key=self.auth_key, db=self.db)

    def close(self):
        if self._connection:
            self._connection.close()
            self._connection = None

    @property
    def connection(self):
        if not self._connection:
            self.connect()
        return self._connection
