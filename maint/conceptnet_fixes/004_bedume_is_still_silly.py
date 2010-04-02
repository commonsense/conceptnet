from csc.conceptnet.models import *
from csc.conceptnet.analogyspace import *
from csc.util import foreach

cnet = conceptnet_2d_from_db('en')
aspace = cnet.svd()

bedume = User.objects.get(username='bedume')
activity = Activity.objects.get(name='administrative fiat')
braw = [r for r in bedume.vote_set.all() if isinstance(r.object, RawAssertion)]
for b in braw:
    if b.object.assertion.relation.name == 'IsA':
        print b.object
        concept = b.object.assertion.concept1.text
        if concept in aspace.u.label_list(0):
            sim = aspace.u[concept,:].hat() * aspace.u['debbie',:].hat()
            if sim > 0.9:
                print sim, b.object
                #b.object.set_rating(bedume, 0, activity)
                #b.object.assertion.set_rating(bedume, 0, activity)

