#!/usr/bin/env python

from csc.conceptnet.models import *
from csc.corpus.models import *
#from django.contrib.auth import *
from django.db import transaction

def check_polarity():
    for a in Assertion.objects.all().select_related('raw'):
        if a.polarity != a.raw.polarity:
            print a.sentence
            print a.raw.sentence
            print a
            print a.raw
            print a.rating_set.all()
            print

#check_polarity()

# conclusion: not worth fixing. The cases where they conflict are all generally
# ugly, but the raw assertions (which we're keeping) are closer to correct.
#
# other conclusion: do not use the old csamoa ratings.

def basically_the_same(s1, s2):
    def canonical(s):
        return s.replace('  ', ' ').strip('. ')
    return canonical(s1) == canonical(s2)

def check_raw_mistakes():
    for ra in RawAssertion.objects.all().select_related('sentence'):
        rawsent = ra.nl_repr()
        sent = ra.sentence.text
        if not basically_the_same(rawsent, sent):
            print ra
            print repr(rawsent)
            print repr(sent)
            print "batch:", ra.batch
            print "predicate:", ra.predicate
            print "frame:", ra.frame.id, ra.frame
            betterone = False
            for r2 in ra.sentence.rawassertion_set.all():
                if basically_the_same(rawsent, r2.nl_repr()):
                    betterone = True
                break
            if ra.predicate is None and betterone:
                print "This raw predicate should be deleted."
            print

@transaction.commit_on_success
def unswitch_raw():
    evilbatch = Batch.objects.get(id=136)
    for ra in RawAssertion.objects.filter(batch=evilbatch).select_related('frame'):
        if ra.predicate is None and ra.frame.id in [1384, 1387, 1420]:
            text1 = ra.text2
            text2 = ra.text1
            ra.text1 = text1
            ra.text2 = text2
            ra.save()
            print ra
            
unswitch_raw()