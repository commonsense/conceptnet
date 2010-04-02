from csc.conceptnet.models import Concept, Assertion, Sentence, Frame
from csc.corpus.models import TaggedSentence
import csv

def dump_assertion_sentences(lang, f):
    writer = csv.writer(f)
    writer.writerow(('id', 'creator', 'score', 'text'))
    for id, username, score, text in Assertion.objects.filter(language=lang).values_list('id','creator__username', 'score','sentence__text').iterator():
        writer.writerow((id, username.encode('utf-8'), score, text.encode('utf-8')))

def dump_all_sentences(lang, f):
    writer = csv.writer(f)
    writer.writerow(('id', 'creator', 'created_on', 'activity', 'text'))
    for id, username, created_on, activity, text in Sentence.objects.filter(language=lang).values_list('id','creator__username','created_on', 'activity__name', 'text').iterator():
        writer.writerow((id, username.encode('utf-8'), created_on,
                         activity, text.encode('utf-8')))

def dump_concepts(lang, f):
    writer = csv.writer(f)
    writer.writerow(('id', 'num_assertions', 'normalized_text', 'canonical_name'))
    for c in Concept.objects.filter(language=lang).iterator():
        writer.writerow((c.id, c.num_predicates, c.text.encode('utf-8'),
                         c.canonical_name.encode('utf-8')))

def dump_assertions(lang, f):
    writer = csv.writer(f)
    writer.writerow(('id', 'sentence', 'relation_type', 'text1', 'text2', 'stem1_id', 'stem2_id', 'frame_id', 'score', 'creator'))
    for id, sentence, relation_type, text1, text2, stem1_id, stem2_id, frame_id, score, creator in Assertion.objects.filter(language=lang).values_list(
        'id', 'sentence__text', 'predtype__name', 'text1', 'text2',
        'stem1_id', 'stem2_id', 'frame_id', 'score', 'creator__username'
        ).iterator():
        writer.writerow((
                id, sentence.encode('utf-8'), relation_type,
                text1.encode('utf-8'), text2.encode('utf-8'),
                stem1_id, stem2_id, frame_id, score,
                creator.encode('utf-8')
                ))

def dump_frames(lang, f):
    writer = csv.writer(f)
    writer.writerow(('id', 'relation_type', 'text', 'goodness'))
    for id, relation_type, text, goodness in Frame.objects.filter(language=lang).values_list(
        'id', 'predtype__name', 'text', 'goodness'
        ).iterator():
        writer.writerow((
                id, relation_type,
                text.encode('utf-8'),
                goodness
                ))

def dump_tagged_sentences(lang, f):
    writer = csv.writer(f)
    writer.writerow(('id', 'text'))
    for id, text in TaggedSentence.objects.filter(language=lang).values_list(
        'id', 'text'
        ).iterator():
        writer.writerow((
                id, text.encode('utf-8')
                ))

if __name__=='__main__':
    import sys
    name, lang = sys.argv

    dump_assertion_sentences(lang, open(lang+'_assertion_sentences.csv','w'))
    dump_all_sentences(lang, open(lang+'_all_sentences.csv','w'))
    dump_concepts(lang, open(lang+'_concepts.csv','w'))
    dump_assertions(lang, open(lang+'_assertions.csv','w'))
    dump_frames(lang, open(lang+'_frames.csv','w'))
