import mongoengine as mon

class Log(mon.Document):
    object = mon.GenericReferenceField()
    action = mon.StringField()
    data = mon.DictField()


