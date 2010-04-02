from csc.conceptnet.models import *
from csc.util import foreach

bedume = User.objects.get(username='bedume')
activity = Activity.objects.get(name='administrative fiat')
braw = [r for r in bedume.vote_set.all() if isinstance(r.object, RawAssertion)]
for b in braw:
    if b.object.assertion.relation.name == 'HasProperty':
        print b.object
        b.object.set_rating(bedume, 0, activity)
        b.object.assertion.set_rating(bedume, 0, activity)

