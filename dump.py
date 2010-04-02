from csc.util import queryset_foreach
from django.core import serializers
from processing import Process

def serialize_qs4e(serializer, querysets, stream, **options):
    qs4e_options = {'transaction': False, 'batch_size': 50}
    for opt in ['batch_size', 'progress_callback', 'transaction']:
        val = options.pop(opt, None)
        if val is not None: qs4e_options[opt] = val

    serializer.options = options
    serializer.options['stream'] = stream
    serializer.stream = stream
    serializer.selected_fields = options.get("fields")

    def serialize_object(obj):
        #import pdb; pdb.set_trace()

        serializer.start_object(obj)
        for field in obj._meta.local_fields:
            if field.serialize:
                if field.rel is None:
                    if serializer.selected_fields is None or field.attname in serializer.selected_fields:
                        serializer.handle_field(obj, field)
                else:
                    if serializer.selected_fields is None or field.attname[:-3] in serializer.selected_fields:
                        serializer.handle_fk_field(obj, field)
        for field in obj._meta.many_to_many:
            if field.serialize:
                if serializer.selected_fields is None or field.attname in serializer.selected_fields:
                    serializer.handle_m2m_field(obj, field)
        serializer.end_object(obj)

    serializer.start_serialization()
    for queryset in querysets:
        queryset_foreach(queryset, serialize_object, **qs4e_options)
    serializer.end_serialization()

def worker(classes):
    for theclass in classes:
        print theclass
        stream = open('db/'+theclass.__name__+'.yaml', 'w')
        querysets = [theclass.objects.all()]
        serialize_qs4e(serializer, querysets, stream)
        stream.close()

serializer = serializers.get_serializer("myyaml")()
from csc.conceptnet4.models import RawAssertion, Assertion, SurfaceForm,\
Frame, Concept, Frequency, Relation, Batch
from csc.corpus.models import Language, Sentence
from csc.nl.models import FunctionClass, FunctionWord
from events.models import Event, Activity
from voting.models import Vote
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
if __name__ == '__main__':
    serializer = serializers.get_serializer("myyaml")()
    from csc.conceptnet4.models import RawAssertion, Assertion, SurfaceForm,\
    Frame, Concept, Frequency, Relation, Batch
    from csc.corpus.models import Language, Sentence
    from csc.nl.models import FunctionClass, FunctionWord
    from events.models import Event, Activity
    from voting.models import Vote
    from django.contrib.auth.models import User
    from django.contrib.contenttypes.models import ContentType
    
    classes = [Vote, RawAssertion, Frame, SurfaceForm, Assertion,
    Relation, Frequency, Concept, FunctionClass, FunctionWord, Language, 
    Sentence, User, ContentType, Activity, Batch]
    
    classes1 = classes[0:5]
    classes2 = classes[5:10]
    classes3 = classes[10:15]
    classes4 = classes[15:]

    for working_set in (classes1, classes2, classes3, classes4):
        proc = Process(target=worker, args=[working_set])
        proc.start()
