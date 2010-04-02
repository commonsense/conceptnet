#!/usr/bin/env python

PREFIX = 'http://conceptnet.media.mit.edu'

from conceptnet.models import Assertion, Frame, RelationType, Concept

import codecs
ofile_raw = open('conceptnet_en_20080604.n3','w')
ofile = codecs.getwriter('utf-8')(ofile_raw)

print >>ofile, '@prefix conceptnet: <%s>.' % (PREFIX+'/')

def prefixed(type, rest):
    return '<%s/%s/%s>' % (PREFIX, type, rest)

def concept(id): return prefixed('concept', id)
def reltype(x): return prefixed('reltype', reltype_id2name[x])
def literal(x): return '"'+x.replace('"','_')+'"'
def _frame(id): return prefixed('frame', id)
def language(x): return prefixed('language', x)
def user(x): return prefixed('user', x)

def proplist(p):
    return u'; '.join(u'conceptnet:%s %s' % (prop, val)
                     for prop, val in p)

reltype_id2name = dict((x.id, x.name) for x in RelationType.objects.all())
frames = set()
concepts = set()

print 'Dumping assertions.'
for (id, stem1_id, reltype_id, stem2_id,
     text1, text2, frame_id, language_id, creator_id,
     score, sentence) in Assertion.useful.filter(language='en').values_list(
    'id', 'stem1_id', 'predtype_id', 'stem2_id',
    'text1', 'text2', 'frame_id', 'language_id', 'creator_id',
    'score', 'sentence__text').iterator():

    ofile.write('<%s/assertion/%s> ' % (PREFIX, id))
    ofile.write(proplist((
        ('LeftConcept', concept(stem1_id)),
        ('RelationType', reltype(reltype_id)),
        ('RightConcept', concept(stem2_id)),
        ('LeftText', literal(text1)),
        ('RightText', literal(text2)),
        ('FrameId', _frame(frame_id)),
        ('Language', language(language_id)),
        ('Creator', user(creator_id)),
        ('Score', score),
        ('Sentence', literal(sentence))
        )))
    ofile.write('.\n')

    frames.add(frame_id)
    concepts.add(stem1_id)
    concepts.add(stem2_id)

ofile.flush()

print 'Dumping frames.'
for id, frame in Frame.objects.in_bulk(list(frames)).iteritems():
    ofile.write(_frame(id)+' ')
    ofile.write(proplist((
                ('RelationType', reltype(frame.predtype_id)),
                ('FrameText', literal(frame.text)),
                ('FrameGoodness', literal(str(frame.goodness)))))
                )
    ofile.write('.\n')

ofile.flush()

print 'Dumping concepts.'
for id, c in Concept.objects.in_bulk(list(concepts)).iteritems():
    ofile.write(concept(id)+' ')
    ofile.write(proplist((
                ('NormalizedText', literal(c.text)),
                ('CanonicalName', literal(c.canonical_name))
                )))
    ofile.write('.\n')


print 'Done.'

ofile.close()
