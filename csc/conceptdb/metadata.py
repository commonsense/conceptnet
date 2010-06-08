from csc.nl import get_nl
import mongoengine as mon

class Dataset(mon.Document):
    name = mon.StringField(required=True, primary_key=True)
    language = mon.StringField()
    
    @property
    def nl():
        if self.language is None:
            raise ValueError("This Dataset is not associated with a natural language")
        return get_nl(self.language)

