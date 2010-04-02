#!/usr/bin/env python
# This one should run in the ConceptNet Django environment.
from csc.conceptnet.models import Concept # just for the environment setup.
from django.db.models import get_models
from django.db.models.query import QuerySet
from csc.util.batch import Status
import sys, sqlite3

models_to_dump = '''
Vote RawAssertion Frame SurfaceForm Assertion
Relation Frequency Concept FunctionClass FunctionWord Language
Sentence User ContentType Activity Batch
'''.strip().split()

models = dict((model.__name__, model) for model in get_models()
              if model.__name__ in models_to_dump)

def dump_to_sqlite(conn):
    cursor = conn.cursor()

    for idx, model_name in enumerate(models_to_dump):
        model = models[model_name]
        print >> sys.stderr, '(%2d/%2d) dumping %s' % (idx+1, len(models_to_dump), model_name)
        meta = model._meta
        db_table = meta.db_table

        truncate = 'DELETE FROM %s' % db_table
        print truncate
        cursor.execute(truncate)

        if model_name == 'User':
            # User is special because we don't want to dump private info.
            placeholder_timestamp = '1969-12-31 19:00:00'
            sql = 'INSERT INTO %s (id, username, last_login, date_joined, first_name, last_name, email, password, is_staff, is_active, is_superuser) VALUES (?, ?, %r, %r, "", "", "", "X", 0, 1, 0)' % (db_table, placeholder_timestamp, placeholder_timestamp)
            queryset = QuerySet(model).values_list('id', 'username')
        else:
            # Okay, so a field has a .serialize parameter on it. But the auto
            # id field has this set to False. Fail. Just serialize all the
            # local fields.
            fields = meta.local_fields
            field_names = [f.column for f in fields]

            sql = 'INSERT INTO %s (%s) VALUES (%s)' % (
                db_table,
                ', '.join(field_names),
                ', '.join('?'*len(fields)))
            queryset = QuerySet(model).values_list(*(field_names)) # hm, this might not work if the db names are different.

        print sql
        cursor.executemany(sql, Status.reporter(queryset, report_interval=1000))
        conn.commit()

    cursor.close()

if __name__ == '__main__':
    db_name = sys.argv[1]
    conn = sqlite3.connect(db_name)
    dump_to_sqlite(conn)

