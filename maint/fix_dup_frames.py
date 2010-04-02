from csc.util import queryset_foreach
from csc.conceptnet4.models import Frame
from django.db import connection
def fix_dups(frame):
    dups = Frame.objects.filter(language=frame.language, text=frame.text,
                                relation=frame.relation)
    for dup in dups:
        if dup.id == frame.id:
            continue
        print dup
        cursor = connection.cursor()
        print("UPDATE raw_assertions SET frame_id=%s WHERE frame_id=%s" % (frame.id, dup.id))
        cursor.execute("UPDATE raw_assertions SET frame_id=%s WHERE frame_id=%s" % (frame.id, dup.id))
        dup.delete()
        print

queryset_foreach(Frame.objects.all().order_by('-goodness', 'id'),
  fix_dups,
  batch_size=100)

