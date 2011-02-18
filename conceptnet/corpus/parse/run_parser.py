#!/usr/bin/env python
import sys, traceback
from csc.conceptnet4.models import Assertion, Batch, RawAssertion, Frame,\
  Frequency, Relation, SurfaceForm, Concept, Rating
from csc.corpus.models import Sentence, Language, Activity
from django.contrib.auth.models import User
from pcfgpattern import pattern_parse
from django.core.paginator import Paginator
from django.db import transaction

csamoa4_activity = Activity.objects.get(name='csamoa4 self-rating')

def process_sentence_delayed(entry, lang, batch):
    frametext, id, matches, reltext = (entry['frametext'], entry['id'],
    entry['matches'], entry['reltext'])
    sentence = Sentence.objects.get(id=id)
    print sentence.text.encode('utf-8')
    
    if reltext is None or reltext == 'junk': return []
    relation = Relation.objects.get(name=reltext)
    text_factors = [lang.nl.lemma_factor(matches[i]) for i in (1, 2)]
    concepts = [Concept.objects.get_or_create(language=lang, text=stem)[0]
                for stem, residue in text_factors]
    for c in concepts: c.save()
    
    surface_forms = [SurfaceForm.objects.get_or_create(concept=concepts[i],
                                                  text=matches[i+1],
                                                  residue=text_factors[i][1],
                                                  language=lang)[0]
                     for i in (0, 1)]
    for s in surface_forms: s.save()
    
    freq, _ = Frequency.objects.get_or_create(text=matches.get('a', ''),
                                              language=lang,
                                              defaults=dict(value=50))
    freq.save()
    
    frame, _ = Frame.objects.get_or_create(relation=relation, language=lang,
                                           text=frametext, frequency=freq,
                                           defaults=dict(goodness=1))
    frame.save()
    
    raw_assertion, _ = RawAssertion.objects.get_or_create(
        surface1=surface_forms[0],
        surface2=surface_forms[1],
        frame=frame,
        language=lang,
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
    assertion.save()
    raw_assertion.assertion = assertion
    raw_assertion.save()
    
    rating1, _ = Rating.objects.get_or_create(
        user=sentence.creator, activity=csamoa4_activity,
        sentence=sentence, score=1
    )
    rating2, _ = Rating.objects.get_or_create(
        user=sentence.creator, activity=csamoa4_activity,
        raw_assertion=raw_assertion, score=1
    )
    rating1.save()
    rating2.save()

    print '=>', str(assertion).encode('utf-8')
    return [assertion]

def process_sentence(sentence, lang, batch):
    print sentence.text.encode('utf-8')
    _, frametext, reltext, matches = pattern_parse(sentence.text)
    
    if reltext is None or reltext == 'junk': return []
    relation = Relation.objects.get(name=reltext)
    text_factors = [lang.nl.lemma_factor(matches[i]) for i in (1, 2)]
    concepts = [Concept.objects.get_or_create(language=lang, text=stem)[0]
                for stem, residue in text_factors]
    for c in concepts: c.save()
    
    surface_forms = [SurfaceForm.objects.get_or_create(concept=concepts[i],
                                                  text=matches[i+1],
                                                  residue=text_factors[i][1],
                                                  language=lang)[0]
                     for i in (0, 1)]
    for s in surface_forms: s.save()
    
    freq, _ = Frequency.objects.get_or_create(text=matches.get('a', ''),
                                              language=lang,
                                              defaults=dict(value=50))
    freq.save()
    
    frame, _ = Frame.objects.get_or_create(relation=relation, language=lang,
                                           text=frametext, frequency=freq,
                                           defaults=dict(goodness=1))
    frame.save()
    
    raw_assertion, _ = RawAssertion.objects.get_or_create(
        surface1=surface_forms[0],
        surface2=surface_forms[1],
        frame=frame,
        language=lang,
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
    assertion.save()
    raw_assertion.assertion = assertion
    raw_assertion.save()
    
    rating1, _ = Rating.objects.get_or_create(
        user=sentence.creator, activity=csamoa4_activity,
        sentence=sentence, score=1
    )
    rating2, _ = Rating.objects.get_or_create(
        user=sentence.creator, activity=csamoa4_activity,
        raw_assertion=raw_assertion, score=1
    )
    rating1.save()
    rating2.save()

    print '=>', str(assertion).encode('utf-8')
    return [assertion]

def run(user, lang, start_page=1):
    batch = Batch()
    batch.owner = user
    
    all_sentences = Sentence.objects.filter(language=lang).order_by('id')
    paginator = Paginator(all_sentences,10)
    #pages = ((i,paginator.page(i)) for i in range(start_page,paginator.num_pages))

    @transaction.commit_on_success
    def do_batch(sentences):
        for sentence in sentences:
            try:
                preds = process_sentence(sentence, lang, batch)
            # changed to an improbable exception for now
            except Exception, e:
                # Add sentence
                e.sentence = sentence

                # Extract traceback
                e_type, e_value, e_tb = sys.exc_info()
                e.tb = "\n".join(traceback.format_exception( e_type, e_value, e_tb ))

                # Raise again
                raise e

    # Process sentences
    page_range = [p for p in paginator.page_range if p >= start_page]
    for i in page_range:
        sentences = paginator.page(i).object_list
        
        # Update progress
        batch.status = "process_sentence_batch " + str(i) + "/" + str(paginator.num_pages)
        batch.progress_num = i
        batch.progress_den = paginator.num_pages
        batch.save()

        try: do_batch(sentences)
        
        except Exception, e: #improbable exception for now
            batch.status = "process_sentence_batch " + str(i) + "/" + str(paginator.num_pages) + " ERROR!"
            batch.remarks = str(e.sentence) + "\n" + str(e) + "\n" + e.tb
            print "***TRACEBACK***"
            print batch.remarks
            batch.save()
            raise e


if __name__ == '__main__':
    user = User.objects.get(username='rspeer')
    lang = Language.get('en')
    run(user, lang, start_page=50000)

