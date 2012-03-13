# commons2.wsgi is configured to live in projects/commons2/deploy.

import os
import sys

# redirect sys.stdout to sys.stderr for bad libraries like geopy that uses
# print statements for optional import exceptions.
sys.stdout = sys.stderr

from os.path import abspath, dirname, join
from site import addsitedir

addsitedir('/srv/conceptnet/lib/python2.6/site-packages')
addsitedir('/usr/lib/pymodules/python2.6')
sys.path.insert(0, '/srv/conceptnet')
sys.path.insert(0, '/srv/conceptnet/conceptnet')
from django.conf import settings
os.environ["DJANGO_SETTINGS_MODULE"] = "conceptnet.django_settings"

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()

