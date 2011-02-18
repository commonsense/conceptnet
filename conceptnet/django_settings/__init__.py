import sys, os

###
### Database configuration
###

# ConceptNet uses a database configuration file to determine how to
#    connect to the database. It's just a normal Python file (e.g.,
#    db_config.py) that contains the Django database settings (see
#    http://docs.djangoproject.com/en/dev/intro/tutorial01/#database-setup
#    or
#    http://docs.djangoproject.com/en/dev/ref/settings/#setting-DATABASE_ENGINE
#
# You just have to tell ConceptNet how to find this file. You can put
# the full path to this file in the CONCEPTNET_DB_CONFIG environment
# variable, or you can put the file on the Python path.
#
# Added bonuses:
# 1. You can use either DATABASE_ or DB_ in your configuration variables.
# 2. If DATABASE_ENGINE is sqlite3, DATABASE_NAME will be treated as relative
#    to the database config file.
# 3. You can use '~' in the environment variable to mean your home directory,
#    like ~/commonsense/db_config.py

if 'CONCEPTNET_DB_CONFIG' in os.environ:
    db_config = {}
    db_config_path = os.path.expanduser(os.environ['CONCEPTNET_DB_CONFIG'])
    db_config_dir = os.path.dirname(db_config_path)
    execfile(db_config_path, db_config)
else:
    try:
        import db_config
        db_config_dir = os.path.abspath(os.path.dirname(db_config.__file__))
        db_config = db_config.__dict__
    except ImportError:
        from conceptnet.django_settings import default_db_config
        db_config = default_db_config.__dict__
        if not os.path.exists(db_config['DB_NAME']):
            from conceptnet.django_settings import db_downloader
            if not db_downloader.prompt_for_download(db_config['DB_NAME']):
                raise SystemExit

def get_db_config(param, default=''):
    long_param = 'DATABASE_'+param
    short_param = 'DB_'+param
    if long_param in db_config: return db_config[long_param]
    if short_param in db_config: return db_config[short_param]
    return default


def relative_to_db_config(path):
    if not os.path.isabs(path):
        path = os.path.join(db_config_dir, path)
    return os.path.normpath(path)


# This sets the Python path to include the distributed libraries.
import csc.lib

DEBUG = db_config.get('DEBUG', False)
TEMPLATE_DEBUG = DEBUG

ADMINS = ()

MANAGERS = ADMINS

DATABASE_ENGINE = get_db_config('ENGINE')    # 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = get_db_config('NAME')        # Or path to database file if using sqlite3.
if DATABASE_ENGINE == 'sqlite3':
    # normalize the path name
    DATABASE_NAME = relative_to_db_config(DATABASE_NAME)
DATABASE_USER = get_db_config('USER', '')        # Not used with sqlite3.
DATABASE_PASSWORD = get_db_config('PASSWORD', '') # Not used with sqlite3.
DATABASE_HOST = get_db_config('HOST', '')        # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = get_db_config('PORT', '')        # Set to empty string for default. Not used with sqlite3.
DATABASE_OPTIONS = get_db_config('OPTIONS', {})

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = ''

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'rebo=05i#a6^%d3m#a=0dzy)cs7(ek%!^nvhwe93n1g4rajas1'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

# Middleware necessary for the admin site.
MIDDLEWARE_CLASSES = (
    # URL normalization, etc.
    'django.middleware.common.CommonMiddleware',
    # Handle sessions.
    'django.contrib.sessions.middleware.SessionMiddleware',
    # Keep track of users.
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

AUTHENTICATION_BACKENDS = (
        'csc.pseudo_auth.backends.LegacyBackend',
        'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'csc.pseudo_auth',
    'csc.corpus',
    'csc.conceptnet',
    'csc.nl',
    'voting',
    'events',
#    'south',
#    'django.contrib.markup',
#    'corpus.parse',
#    'realm',
)

# Install django_evolution, if available.
USE_DJANGO_EVOLUTION = False
if USE_DJANGO_EVOLUTION:
    try:
        import django_evolution
        INSTALLED_APPS += ('django_evolution',)
    except ImportError:
        pass

# Serve the API if we can.
SERVE_API = db_config.get('SERVE_API', False)
if SERVE_API:
    try:
        import csc.webapi
        import csc.webapi.handlers
        INSTALLED_APPS += ('csc.webapi',)
    except ImportError:
        pass

# Install command extensions, if available.
try:
    import django_extensions
    INSTALLED_APPS += ('django_extensions',)
except ImportError:
    pass
    
# Use memcache if available.
memcache = False
try:
    import cmemcache
    memcache = True
except ImportError:
    try:
        import memcache
        memcache = True
    except ImportError:
        pass

if memcache:
    CACHE_BACKEND="memcached://127.0.0.1:11211"

## YAML serialization is no longer important.
#SERIALIZATION_MODULES = {
#    'myyaml': 'serialize.pyyaml'
#}

class PsycoMiddleware(object):
    """
    This middleware enables the psyco extension module which can massively
    speed up the execution of any Python code.
    """
    def process_request(self, request):
        try:
            import psyco
            psyco.full()
        except ImportError:
            pass
        return None
