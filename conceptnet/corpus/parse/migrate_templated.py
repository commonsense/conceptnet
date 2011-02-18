#!/usr/bin/env python
import sys, traceback
from conceptnet4.models import Assertion, Batch, RawAssertion, Frame,\
  Frequency, Relation, SurfaceForm, Concept, Rating
import conceptnet.models as cn3
from corpus.models import Sentence, Language, Activity
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from corpus.parse.adverbs import map_adverb
from itertools import islice
import yaml

csamoa4_activity = Activity.objects.get(name='csamoa4 self-rating')
good_acts = [ 16, 20, 22, 24, 28, 31, 32 ]
en = Language.get('en')

def process_predicate(pred, batch):
    frametext = pred.frame.text
    matches = {1: pred.text1, 2: pred.text2}
    if pred.polarity < 0: matches['a'] = 'not'
    relation = pred.relation
    sentence = pred.sentence
    lang = pred.language

    surface_forms = [SurfaceForm.get(matches[i], lang, auto_create=True)
                     for i in (1, 2)]
    concepts = [s.concept for s in surface_forms]
    
    # FIXME: english only so far
    freq = map_adverb(matches.get('a', ''))
    relation = Relation.objects.get(id=relation.id)
    frame, _ = Frame.objects.get_or_create(relation=relation, language=lang,
                                           text=frametext,
                                           defaults=dict(frequency=freq, 
                                                         goodness=1))
    frame.save()
    
    raw_assertion, _ = RawAssertion.objects.get_or_create(
        surface1=surface_forms[0],
        surface2=surface_forms[1],
        frame=frame,
        language=lang,
        creator=sentence.creator,
        defaults=dict(batch=batch))
    # still need to set assertion_id
    
    assertion, _ = Assertion.objects.get_or_create(
        relation=relation,
        concept1=concepts[0],
        concept2=concepts[1],
        frequency=freq,
        language=lang,
        defaults=dict(score=0)
    )
    #assertion.save()
    
    raw_assertion.assertion = assertion
    raw_assertion.sentence = sentence
    raw_assertion.save()

    sentence.set_rating(sentence.creator, 1, csamoa4_activity)
    raw_assertion.set_rating(sentence.creator, 1, csamoa4_activity)
    assertion.set_rating(sentence.creator, 1, csamoa4_activity)

    for rating in pred.rating_set.all():
        score = rating.rating_value.deltascore
        if score < -1: score = -1
        if score > 1: score = 1
        if rating.activity_id is None:
            rating_activity = Activity.objects.get(name='unknown')
        else:
            rating_activity = rating.activity
        sentence.set_rating(rating.user, score, rating_activity)
        raw_assertion.set_rating(rating.user, score, rating_activity)
        assertion.set_rating(rating.user, score, rating_activity)

    print '=>', unicode(assertion).encode('utf-8')
    return [assertion]

def run(user, start_page=1):
    batch = Batch()
    batch.owner = user
    
    #generator = yaml.load_all(open('delayed_test.yaml'))
    #all_entries = list(generator)
    all_preds = []
    for actid in good_acts:
        all_preds.extend(cn3.Predicate.objects.filter(sentence__activity__id=actid, language=en))
    paginator = Paginator(all_preds,100)
    #pages = ((i,paginator.page(i)) for i in range(start_page,paginator.num_pages))

    @transaction.commit_on_success
    def do_batch(entries):
        for entry in entries:
            try:
                preds = process_predicate(entry, batch)
            # changed to an improbable exception for now
            except ZeroDivisionError, e:
                # Add entry
                e.entry = entry

                # Extract traceback
                e_type, e_value, e_tb = sys.exc_info()
                e.tb = "\n".join(traceback.format_exception( e_type, e_value, e_tb ))

                # Raise again
                raise e

    # Process entries
    page_range = [p for p in paginator.page_range if p >= start_page]
    for i in page_range:
        entries = paginator.page(i).object_list
        
        # Update progress
        batch.status = "process_entry_batch " + str(i) + "/" + str(paginator.num_pages)
        batch.progress_num = i
        batch.progress_den = paginator.num_pages
        batch.save()

        try: do_batch(entries)
        
        except ZeroDivisionError, e:
            batch.status = "process_entry_batch " + str(i) + "/" + str(paginator.num_pages) + " ERROR!"
            batch.remarks = str(e.entry) + "\n" + str(e) + "\n" + e.tb
            print "***TRACEBACK***"
            print batch.remarks
            batch.save()
            raise e

if __name__ == '__main__':
    user = User.objects.get(username='rspeer')
    run(user, start_page=164)

