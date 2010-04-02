#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csamoa
from conceptnet4.models import Assertion, Batch, RawAssertion, Frame,\
  Frequency, Relation, SurfaceForm, Concept
import conceptnet.models as cn3
from corpus.models import Sentence, Language, Activity
from django.contrib.auth.models import User
from itertools import islice
import yaml
from csc.util import queryset_foreach

csamoa4_activity = Activity.objects.get(name='csamoa4 self-rating')
def process_predicate(pred):
    frametext = pred.frame.text
    relation = Relation.objects.get(id=pred.relation.id)
    sentence = pred.sentence
    lang = pred.language
    if pred.polarity < 0:
        freq, c = Frequency.objects.get_or_create(value=-5, language=lang,
        defaults=dict(text='[negative]'))
    else:
        freq, c = Frequency.objects.get_or_create(value=5, language=lang,
        defaults=dict(text=''))
    if c: freq.save()

    frame, c = Frame.objects.get_or_create(relation=relation, language=lang,
                                           text=frametext,
                                           defaults=dict(frequency=freq, 
                                                         goodness=1))
    if c: frame.save()
    raw_assertion = RawAssertion.make(sentence.creator, frame, pred.text1,
    pred.text2, csamoa4_activity, 1)
    assertion = raw_assertion.assertion
    
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
    return raw_assertion

def run():
    #generator = yaml.load_all(open('delayed_test.yaml'))
    #all_entries = list(generator)

    #activity_filter = Q()
    #for actid in good_acts:
    #    activity_filter |= Q(sentence__activity__id=actid)
    for lang in ['it', 'fr', 'nl', 'es', 'pt']:
        queryset_foreach(cn3.Predicate.objects.filter(language__id=lang),
        process_predicate, batch_size=10)

if __name__ == '__main__':
    run()

