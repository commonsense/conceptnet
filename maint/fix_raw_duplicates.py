from csc.util import queryset_foreach
from conceptnet4.models import Sentence, Assertion, RawAssertion, Vote

def check_for_dupes(r):
    for other in RawAssertion.objects.filter(surface1=r.surface1,
    surface2=r.surface2, frame=r.frame, id__gt=r.id):
        for vote in other.votes.all():
            nvotes = Vote.objects.filter(user=vote.user,
            object_id=r.id).count()
            if nvotes == 0:
                vote.object = r
                vote.save()
            else:
                vote.delete()
        other.delete()
    r.update_score()

if __name__ == '__main__':
    queryset_foreach(RawAssertion.objects.all(), check_for_dupes,
    batch_size=10)

