import logging
import os
import sqlite3

from collections import OrderedDict

from sqlalchemy.exc import OperationalError

from telegerrit import settings


logger = logging.getLogger(__name__)


class WritersException(Exception):
    pass


class SettingsWriter(object):

    db_path = settings.db_path
    _conn = None
    table_name = None  # name of the table to be created
    columns = None

    @classmethod
    def from_row(cls, row):
        return dict(zip(cls.columns, row))

    @classmethod
    def __prepared(cls):
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
        except sqlite3.OperationalError:
            return False

        c = conn.cursor()
        cols = ','.join(map(lambda x: x[0] + ' ' + x[1], cls.columns.items()))
        sql = 'CREATE TABLE IF NOT EXISTS {tn} ({cols})'.format(
            tn=cls.table_name, cols=cols)
        # Creating a new SQLite table with 1 column
        try:
            c.execute(sql)
        except sqlite3.OperationalError as e:
            logger.critical(e)

        conn.commit()

        return True

    @classmethod
    def __exec_sql(cls, sql):
        if not cls.__prepared():
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
    def retrieve(cls, **data):
        query = ' AND '.join(
            [unicode(k) + '="' + unicode(v)+'"' for k, v in data.items()])

        sql = "SELECT * FROM {table_name} WHERE {query}".format(
            table_name=cls.table_name, query=query)

        return cls.__exec_sql(sql)

    @classmethod
    def get_one(cls, **data):
        return cls.retrieve(**data).fetchone()

    @classmethod
    def get_many(cls, **data):
        return cls.retrieve(**data).fetchall()

    @classmethod
    def update(cls, values, **query):
        q = ' AND '.join(
            [unicode(k) + '=' + unicode(v) for k, v in query.items()])
        values = ','.join(
            [unicode(k)+'='+unicode(v) for k, v in values.items()])

        sql = "UPDATE {table_name} SET {values} WHERE {query}".format(
            table_name=cls.table_name, values=values, query=q)

        return cls.__exec_sql(sql).fetchall()

    @classmethod
    def delete(cls, **params):
        q = ' AND '.join(
            [unicode(k)+'="'+unicode(v)+'"' for k, v in params.items()])

        sql = "DELETE FROM {table_name} WHERE {query}".format(
            table_name=cls.table_name, query=q)
        return cls.__exec_sql(sql)


class CommentsWriter(SettingsWriter):
    """Manager for setting for comment"""

    table_name = 'Comments'
    # TODO unique by chat_id
    columns = OrderedDict({
        'chat_id': 'INTEGER',
        'is_notified': 'INTEGER',
    })

    @classmethod
    def save(cls, chat_id, is_notified):
        return super(CommentsWriter, cls).save(
            chat_id=chat_id, is_notified=is_notified)


class UserMap(SettingsWriter):
    """Manager for setting map gerrit username to telegram user id"""

    table_name = 'UserMap'
    # TODO uniq by all cols
    columns = OrderedDict({
        'chat_id': 'INTEGER',
        'gerrit_username': 'INTEGER',
    })

    @classmethod
    def get_by_gerrit_username(cls, username):
        try:
            data = super(UserMap, cls).get_one(gerrit_username=username)
        except WritersException:
            data = None
        else:
            return data[1]

    @classmethod
    def set(cls, **data):
        rows = cls.get_many(chat_id=data.get('chat_id'))
        for row in rows:
            param = cls.from_row(row)
            param.pop('gerrit_username')
            cls.delete(**param)

        return cls.save(**data)
