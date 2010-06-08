from csc.nl import get_nl
import mongoengine as mon

class Language(mon.Document):
    name = mon.StringField(required=True, primary_key=True)

    @property
    def nl():
        return get_nl(self.name)

class Dataset(mon.Document):
    name = mon.StringField(required=True, primary_key=True)
    language = mon.ReferenceField(Language)
