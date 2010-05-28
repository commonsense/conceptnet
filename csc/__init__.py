# The following line MUST be the only line in this file, according to the setuptools docs:
__import__('pkg_resources').declare_namespace(__name__)
# But you also need the following for py2exe to work, according to http://www.py2exe.org/index.cgi/ExeWithEggs
import modulefinder
for p in __path__:
   modulefinder.AddPackagePath(__name__, p)
