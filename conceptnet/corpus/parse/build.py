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

def process_yaml(entry, lang, batch):
    if entry is None: return []
    frametext, id, matches, reltext = (entry['frametext'], entry['id'],
    entry['matches'], entry['reltext'])
    sentence = Sentence.objects.get(id=id)
    print sentence.text.encode('utf-8')
    if sentence.activity.id in good_acts:
        print "(we have a better parse)"
        return []
    if (sentence.text.startswith('Situation:')
        or sentence.text.startswith('The statement')
        or sentence.text.startswith('To understand')
        or sentence.text.startswith('In the event')):
            print "* skipped *"
            return []
    if matches.get(2).startswith('do the following'):
        print "** skipped **"
        return []
    
    if reltext is None or reltext == 'junk': return []

    # quick fixes
    if reltext == 'AtLocation' and matches.get('a') == 'of': return []
    if reltext == 'AtLocation' and matches.get('a') == 'near':
        reltext = 'LocatedNear'
    if reltext in ['IsA', 'CapableOf'] and matches.get('a') in ['in', 'on', 'at', 'by']:
        reltext = 'AtLocation'
        matches['a'] = ''
    for val in matches.values():
        if len(val.split()) > 6:
            # we'd rather wait to parse this better.
            return []

    relation = Relation.objects.get(name=reltext)
    
    surface_forms = [SurfaceForm.get(matches[i], lang, auto_create=True)
                     for i in (1, 2)]
    concepts = [s.concept for s in surface_forms]

    # FIXME: english only so far
    freq = map_adverb(matches.get('a', ''))
    
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
    assertion.score += 1
    #assertion.save()
    
    raw_assertion.assertion = assertion
    raw_assertion.sentence = sentence
    raw_assertion.save()

    sentence.set_rating(sentence.creator, 1, csamoa4_activity)
    raw_assertion.set_rating(sentence.creator, 1, csamoa4_activity)
    assertion.set_rating(sentence.creator, 1, csamoa4_activity)

    for old_raw in cn3.RawAssertion.objects.filter(sentence=sentence):
        pred = old_raw.predicate
        if not pred: continue
        for rating in pred.rating_set.all():
            score = rating.rating_value.deltascore
            if score > 0: score = 1
            if score < 0: score = -1
            if rating.activity_id is None:
                rating_activity = Activity.objects.get(name='unknown')
            else:
                rating_activity = rating.activity
            sentence.set_rating(rating.user, score, rating_activity)
            raw_assertion.set_rating(rating.user, score, rating_activity)
            assertion.set_rating(rating.user, score, rating_activity)
    
    print '=>', unicode(assertion).encode('utf-8')
    return [assertion]

def run(user, lang, start_page=1):
    batch = Batch()
    batch.owner = user
    
    #generator = yaml.load_all(open('delayed_test.yaml'))
    #all_entries = list(generator)
    all_entries = pickle.load(open('yamlparsed.pickle'))
    paginator = Paginator(all_entries,100)
    #pages = ((i,paginator.page(i)) for i in range(start_page,paginator.num_pages))

    @transaction.commit_on_success
    def do_batch(entries):
        for entry in entries:
            try:
                preds = process_yaml(entry, lang, batch)
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

import migrate_templated
if __name__ == '__main__':
    user = User.objects.get(username='rspeer')
    lang = Language.get('en')
    run(user, lang, start_page=214)
    migrate_templated.run(user, start_page=1)

