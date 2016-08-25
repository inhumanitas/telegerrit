import os

import sqlite3
from sqlalchemy.exc import OperationalError

from telegerrit import settings


class WritersException(Exception):
    pass


class SettingsWriter(object):

    db_path = settings.db_path
    _conn = None
    table_name = None  # name of the table to be created
    columns = None

    @classmethod
    def prepared(cls):
        # Connecting to the database file
        db_path = os.path.dirname(cls.db_path)
        if not os.path.exists(db_path):
            try:
                os.mkdir(db_path)
            except OSError:
                # return False
                pass
        try:
            cls._conn = conn = sqlite3.connect(cls.db_path)
        except OperationalError:
            return False

        c = conn.cursor()
        cols = ','.join(map(lambda x: x[0] + ' ' + x[1], cls.columns.items()))
        sql = 'CREATE TABLE IF NOT EXISTS {tn} ({cols})'.format(
            tn=cls.table_name, cols=cols)
        # Creating a new SQLite table with 1 column
        try:
            c.execute(sql)
        except OperationalError:
            pass

        conn.commit()

        return True

    @classmethod
    def __exec_sql(cls, sql):
        if not cls.prepared():
            raise WritersException("Could not access to DB")

        try:
            result = cls._conn.execute(sql)
            cls._conn.commit()
        except sqlite3.IntegrityError as e:
            raise WritersException("Error while saving data: {0}".format(e))

        return result

    @classmethod
    def __write_entry(cls, **data):

        columns = ','.join(cls.columns.keys())
        values = ','.join(['"' + unicode(v) + '"' for v in data.values()])

        sql = "INSERT INTO {table_name} ({cols}) VALUES ({values})".format(
            table_name=cls.table_name, cols=columns, values=values)

        return cls.__exec_sql(sql)

    @classmethod
    def save(cls, **data):
        return cls.__write_entry(**data)

    @classmethod
    def get(cls, **data):

        query = ' AND '.join(
            [unicode(k) + '=' + unicode(v) for k, v in data.items()])

        sql = "SELECT * FROM {table_name} WHERE {query}".format(
            table_name=cls.table_name, query=query)

        return cls.__exec_sql(sql).fetchall()

    @classmethod
    def update(cls, values, **query):
        q = ' AND '.join(
            [unicode(k) + '=' + unicode(v) for k, v in query.items()])
        values = ','.join(
            [unicode(k)+'='+unicode(v) for k, v in values.items()])

        sql = "UPDATE {table_name} SET {values} WHERE {query}".format(
            table_name=cls.table_name, values=values, query=q)

        return cls.__exec_sql(sql).fetchall()


class CommentsWriter(SettingsWriter):
    """Manager for setting for comment"""

    table_name = 'Comments'
    columns = {
        'chat_id': 'INTEGER',
        'is_notified': 'INTEGER',
    }

    @classmethod
    def save(cls, chat_id, is_notified):
        return super(CommentsWriter, cls).save(
            chat_id=chat_id, is_notified=is_notified)

    @classmethod
    def get(cls, chat_id):
        return super(CommentsWriter, cls).get(chat_id=chat_id)
