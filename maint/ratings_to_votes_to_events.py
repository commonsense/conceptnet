import sys
sys.path.insert(0, '..')
import settings
from util import queryset_foreach
from events.models import Event
from voting.models import Vote
from datetime import datetime
from conceptnet4.models import Rating

def rating_to_vote(r):
    obj = r.sentence or r.raw_assertion or r.assertion
    score = 0
    if r.score > 0: score=1
    if r.score < 0: score=-1
    Vote.objects.record_vote(obj, r.user, score)
    ev = Event.record_event(obj, r.user, r.activity)
    ev.timestamp = r.updated
    ev.save()

def progress_callback(num, den):
    print num, '/', den

queryset_foreach(Rating.objects.all(), rating_to_vote)

