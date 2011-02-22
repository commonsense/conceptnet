#!/usr/bin/env python
import sys
db_name = sys.argv[1]

from django.conf import settings
settings.configure(
    DATABASE_ENGINE = 'sqlite3',
    DATABASE_NAME = db_name,
    INSTALLED_APPS=(
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'csc.corpus',
        'csc.conceptnet',
        'csc.nl',
        'voting',
        'events',
        'south'))

from django.core.management import call_command
call_command('syncdb')
call_command('migrate')

