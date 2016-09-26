import logging
import os

import sqlite3


from collections import OrderedDict
from telegerrit import settings


logger = logging.getLogger(__name__)


# TODO Refactor to ORM usage

class WritersException(Exception):
    pass


class SettingsWriter(object):

    db_path = settings.db_path
    _conn = None
    table_name = None  # name of the table to be created
    columns = None

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
        cols = u','.join(map(lambda x: x[0] + u' ' + x[1], cls.columns.items()))
        sql = u'CREATE TABLE IF NOT EXISTS {tn} ({cols})'.format(
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

        columns = u','.join(cls.columns.keys())
        values = u','.join([u'"' + unicode(v) + u'"' for v in data.values()])

        sql = u"INSERT INTO {table_name} ({cols}) VALUES ({values})".format(
            table_name=cls.table_name, cols=columns, values=values)

        return cls.__exec_sql(sql)

    @classmethod
    def save(cls, **data):
        return cls.__write_entry(**data)

    @classmethod
    def get(cls, **data):

        query = u' AND '.join(
            [unicode(k) + u'="' + unicode(v)+u'"' for k, v in data.items()])

        sql = u"SELECT * FROM {table_name} WHERE {query}".format(
            table_name=cls.table_name, query=query)

        return cls.__exec_sql(sql).fetchone()

    @classmethod
    def get_many(cls, **data):

        query = u' AND '.join(
            [unicode(k) + u'="' + unicode(v) + u'"' for k, v in data.items()])
        if query:
            sql = u"SELECT * FROM {table_name} WHERE {query}".format(
                table_name=cls.table_name, query=query)
        else:
            return cls.get_all()
        return cls.__exec_sql(sql).fetchall()

    @classmethod
    def update(cls, values, **query):
        q = u' AND '.join(
            [unicode(k) + u'=' + unicode(v) for k, v in query.items()])
        values = u','.join(
            [unicode(k) + u'= "'+unicode(v) + u'"' for k, v in values.items()])
        if q:
            sql = u"UPDATE {table_name} SET {values} WHERE {query}".format(
                table_name=cls.table_name, values=values, query=q)
        else:
            sql = u"UPDATE {table_name} SET {values}".format(
                table_name=cls.table_name, values=values)

        return cls.__exec_sql(sql).fetchall()

    @classmethod
    def get_all(cls):
        sql = u"SELECT * FROM {table_name}".format(
                table_name=cls.table_name)
        return cls.__exec_sql(sql).fetchall()


class CommentsWriter(SettingsWriter):
    """Manager for setting for comment"""

    table_name = 'Comments'
    columns = OrderedDict({
        'chat_id': 'INTEGER',
        'is_notified': 'INTEGER',
    })
    # TODO unique by chat_id

    @classmethod
    def save(cls, chat_id, is_notified):
        query = {'chat_id': chat_id}

        if CommentsWriter.get(**query):
            CommentsWriter.update(values={'is_notified': is_notified},
                                  **query)
        else:
            super(CommentsWriter, cls).save(**query)

        return True

    @classmethod
    def is_notified(cls, chat_id):
        row = CommentsWriter.get(chat_id=chat_id)
        is_notified, chat_id = row if row else ('False', 0)
        is_notified = is_notified == 'True'
        return is_notified


class UserMap(SettingsWriter):
    """Manager for setting map gerrit username to telegram user id"""

    table_name = 'UserMap'
    columns = OrderedDict({
        'chat_id': 'INTEGER',
        'gerrit_username': 'INTEGER',
    })

    # TODO uniq by all cols

    @classmethod
    def save(cls, **data):
        query = {'chat_id': data['chat_id']}

        if UserMap.get(**query):
            UserMap.update(values={'gerrit_username': data['gerrit_username']},
                           **query)
        else:
            super(UserMap, cls).save(**data)

        return True

    @classmethod
    def get_by_gerrit_username(cls, username):
        chat_id = None
        try:
            row = super(UserMap, cls).get(gerrit_username=username)
        except WritersException:
            row = None
        if row:
            chat_id, user_name = row
        return chat_id

    @classmethod
    def get_user_ids(cls):
        rows = super(UserMap, cls).get_many()
        for chat_id, user_name in rows:
            yield chat_id
