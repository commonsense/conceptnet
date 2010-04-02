#!/usr/bin/env python
import sys, os
if 'DJANGO_SETTINGS_MODULE' not in os.environ:
    print "Setting DJANGO_SETTINGS_MODULE=csamoa.settings temporarily."
    print "You may want to set that more permanently in your environment."
    print
    os.environ['DJANGO_SETTINGS_MODULE'] = 'csc.django_settings'

from csc.conceptnet.models import User
from csc.corpus.models import Sentence
from votes.models import Vote
from django.db import transaction, connection
from django.conf import settings

try:
    cursor = connection.cursor()
except:
    print "Problem while connecting to the database. Check your db_config.py."
    print "Original error:"
    raise

users_table_error = """
Use this script ONLY if you have just created a fresh ConceptNet
database, imported the dump from the website, and ran
`./manage.py syncdb` to add the Django tables.

When running `syncdb`, DO NOT create an admin user. It will conflict
with a user that this script will add.
"""

try:
    if User.objects.all().count() > 0:
        print "Refusing to run because you already have users in the database."
        print
        print users_table_error
        print "Original error:"
        sys.exit(1)
except:
    print """
Encountered a problem checking the users table (auth_user). Maybe it
doesn't exist?"""
    print
    print users_table_error
    print "Original error:"
    raise


## Now the real work.

print "Getting all known uids... ",
# All Assertions have Sentences, which have the same creator. So the Sentences
# is the most complete list of users.
print "(users...) ",
uids = set(Sentence.objects.all().values_list('creator__id', flat=True).iterator())
# But some users may have been raters only.
print "(ratings...) ",
for uid in Vote.objects.all().values_list('user__id', flat=True).iterator():
    uids.add(uid)
print

@transaction.commit_on_success
def make_users(uids):
    for uid in uids:
        User.objects.create(id=uid, username='user_%d' % uid)

print "Creating %d placeholder users..." % len(uids)
make_users(uids)

if settings.DATABASE_ENGINE in ('postgresql_psycopg2', 'postgresql'):
    print "Resetting id sequence for PostgreSQL..."
    seq = 'auth_user_id_seq'
    cursor.execute('ALTER SEQUENCE %s RESTART WITH %d;' % (seq, max(uids)+1))
