from rethinkdb import ast

import remodel.connection


run = ast.RqlQuery.run

def remodel_run(self, c=None, **global_optargs):
    """
    Passes a connection from the connection pool so that we can call .run()
    on a query without an explicit connection
    """

    if not c:
        with remodel.connection.get_conn() as conn:
            return run(self, conn, **global_optargs)
    else:
        return run(self, c, **global_optargs)

ast.RqlQuery.run = remodel_run
