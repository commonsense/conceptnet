#!/usr/bin/env python
from csc.conceptnet.models import *
from csc.corpus.models import *
from django.contrib.auth import *
from django.db import transaction

den = Assertion.objects.filter(raw__isnull=True).count()

# Add raw assertions to predicates created on Ruby Commons.
if den > 0:
    batch = Batch(owner=User.objects.get(id=20003),
        remarks="creating raw assertions for ruby commons",
        progress_den=den)
    batch.save()
    
    num = 0
    for a in Assertion.objects.filter(raw__isnull=True):
        raw = RawAssertion(batch=batch, frame=a.frame, predtype=a.predtype,
                           text1=a.text1, text2=a.text2, polarity=a.polarity,
                           modality=a.modality, sentence=a.sentence,
                           language=a.language, predicate=a)
        raw.save()
        a.raw = raw
        a.save()
        num += 1
        batch.progress_num = num
        batch.save()
        print num, '/', den, raw

# Some raw assertions have text1 and text2 switched, and this was fixed after
# the fact in their predicates. Fix that.
@transaction.commit_on_success
def switch_raw():
    i = 0
    for a in Assertion.objects.all().select_related('raw'):
        if i % 1000 == 0: print i
        i += 1
        if (a.language.nl.normalize(a.text1) == a.language.nl.normalize(a.raw.text2) and
            a.language.nl.normalize(a.text2) == a.language.nl.normalize(a.raw.text1) and
            a.stem1.text != a.stem2.text):
            t1, t2 = a.raw.text2, a.raw.text1
            a.raw.text1 = t1
            a.raw.text2 = t2
            a.raw.save()
            print a
            print a.raw
            print

switch_raw()

#for a in Assertion.objects.all():
#    if a.text1 != a.raw.text1 or a.text2 != a.raw.text2:
#        print a.text1, '/', a.text2, a
#        print a.raw
#        print
