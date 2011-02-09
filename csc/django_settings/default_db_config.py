import os

# Don't use a "dot" directory on Windows. It might make Windows sad.
if os.name == 'nt':
    user_data_dir = os.path.expanduser('~/conceptnet/')
else:
    user_data_dir = os.path.expanduser('~/.conceptnet/')

DB_ENGINE = "sqlite3"
DB_NAME = user_data_dir + "ConceptNet.db"
DB_HOST = ""
DB_PORT = ""
DB_USER = ""
DB_PASSWORD = ""
DB_SCHEMAS = ""

DEBUG = True
SERVE_API = True
