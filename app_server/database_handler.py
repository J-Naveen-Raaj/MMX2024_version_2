import os

import sqlalchemy as db
from sqlalchemy import text

from app_server.custom_logger import get_logger

logger = get_logger(__name__)




def get_sqlite_url():
    CURR_DIR = os.path.dirname(__file__)
    database_path = os.path.join(CURR_DIR, "mmo.db")
    connection_string = f"sqlite:///{database_path}"
    connect_args = {"check_same_thread": False}
    return connection_string, connect_args


class DatabaseHandler(object):
    """
    class which handles all the db operations
    """

    def get_database_conn(self):
        """
        Method to get database connection (mysql)
        :return: self object
        """
        # username = results_db['username']
        # password = results_db['password']
        # database_name = results_db['username']
        # port = results_db['port']
        # host = results_db['host']
        # Create a connection string
        connection_string, connect_args = get_sqlite_url()
        engine = db.create_engine(
            connection_string, echo=False, connect_args=connect_args
        )

        try:
            self.conn = engine.connect()
        except db.exc.OperationalError:
            print("postgres not accessible")
            print("trying sqlite")
            connection_string, connect_args = get_sqlite_url()
            engine = db.create_engine(
                connection_string, echo=False, connect_args=connect_args
            )
            self.conn = engine.connect()
        print("sqlalchemy connection established")
        self.conn.row_factory = dict_factory
        self.conn.engine = engine

        return self

    def get_database_conn_without_factory(self):
        """
        Method to get database connection (mysql)
        :return: self object
        """
        # username = results_db['username']
        # password = results_db['password']
        # database_name = results_db['username']
        # port = results_db['port']
        # host = results_db['host']\
        connection_string, connect_args = get_sqlite_url()
        engine = db.create_engine(
            connection_string, echo=False, connect_args=connect_args
        )

        try:
            conn = engine.connect()
        except db.exc.OperationalError:
            print("postgres not accessible")
            print("trying sqlite")
            connection_string, connect_args = get_sqlite_url()
            engine = db.create_engine(
                connection_string, echo=False, connect_args=connect_args
            )
            conn = engine.connect()
        return conn

    def processquery(self, query, arguments=(), return_id=False):
        """
        method to execute the query and fetch the result if required
        :param query:
        :param arguments:
        :param return_id:
        :return: result set
        """
        # logger.info("In processquery")
        # logger.info(query)
        # logger.info(arguments)
        cursor = self.conn
        result = cursor.execute(text(query), arguments)
        # result = [row for row in result]

        if return_id:
            return result.lastrowid

        result = [r._asdict() for r in result]
        # result = []
        # result = cursor.fetchall()
        # logger.info(result)
        return result

    def processqueryinsert(self, query, arguments=None, return_id=False):
        """
                method to execute the query and fetch the result if required
        :param query:
        :param arguments:
        :param return_id:
        :return: result set
        """
        # logger.info("In processquery")
        # logger.info(query)
        # logger.info(arguments)

        if arguments is None:
            arguments = {}

        result = self.conn.execute(text(query), arguments)

        if return_id:
            return result.lastrowid

        return result

    def save_db(self):
        self.conn.commit()


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
