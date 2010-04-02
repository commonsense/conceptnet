from csc.conceptnet4.models import *
from events.models import Event, Activity
from voting.models import Vote
from csc.util import queryset_foreach

def nuke_it(event):
    object = event.object
    if object is None: return
    for vote in object.votes.all():
        vote.delete()
    object.delete()

#queryset_foreach(Event.objects.filter(content_type__id=92, activity__id=41),
#nuke_it, 50)
queryset_foreach(Event.objects.filter(content_type__id=90, activity__id=41),
nuke_it, 50)
queryset_foreach(Event.objects.filter(content_type__id=20, activity__id=41),
nuke_it, 50)

