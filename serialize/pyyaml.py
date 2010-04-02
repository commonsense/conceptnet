"""
Improved YAML serializer by rspeer@mit.edu. Uses a stream of documents so that
it doesn't have to keep all database entries in memory.

Requires PyYaml (http://pyyaml.org/), but that's checked for in __init__.

To use it, add a line like this to your settings.py::
  
  SERIALIZATION_MODULES = {
      'yaml': 'path.to.import.this.module'
  }
"""

from StringIO import StringIO
import yaml
from django.utils.encoding import smart_unicode

try:
    import decimal
except ImportError:
    from django.utils import _decimal as decimal # Python 2.3 fallback

from django.db import models
from django.core.serializers.python import Serializer as PythonSerializer
from django.core.serializers.python import Deserializer as PythonDeserializer

class DjangoSafeDumper(yaml.SafeDumper):
    def represent_decimal(self, data):
        return self.represent_scalar('tag:yaml.org,2002:str', str(data))

DjangoSafeDumper.add_representer(decimal.Decimal, DjangoSafeDumper.represent_decimal)

class Serializer(PythonSerializer):
    """
    Convert a queryset to YAML.
    """
    
    internal_use_only = False
    
    def handle_field(self, obj, field):
        # A nasty special case: base YAML doesn't support serialization of time
        # types (as opposed to dates or datetimes, which it does support). Since
        # we want to use the "safe" serializer for better interoperability, we
        # need to do something with those pesky times. Converting 'em to strings
        # isn't perfect, but it's better than a "!!python/time" type which would
        # halt deserialization under any other language.
        if isinstance(field, models.TimeField) and getattr(obj, field.name) is not None:
            self._current[field.name] = str(getattr(obj, field.name))
        else:
            super(Serializer, self).handle_field(obj, field)
    
    def end_object(self, obj):
        the_object = {
            "model"  : smart_unicode(obj._meta),
            "pk"     : smart_unicode(obj._get_pk_val(), strings_only=True),
            "fields" : self._current
        }
        self._current = None
        dumpstr = yaml.dump(the_object, Dumper=DjangoSafeDumper,
        explicit_start=True, **self.options)
        self.stream.write(dumpstr)

    def start_serialization(self):
        self.options.pop('stream', None)
        self.options.pop('fields', None)
        PythonSerializer.start_serialization(self)

    def end_serialization(self):
        self.stream.close()

    def getvalue(self):
        return self.stream.getvalue()

def Deserializer(stream_or_string, **options):
    """
    Deserialize a stream or string of YAML data.
    """
    if isinstance(stream_or_string, basestring):
        stream = StringIO(stream_or_string)
    else:
        stream = stream_or_string
    for obj in PythonDeserializer(yaml.load_all(stream)):
        yield obj

