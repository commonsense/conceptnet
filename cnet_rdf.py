#!/usr/bin/env python

PREFIX = 'http://conceptnet.media.mit.edu/'

from conceptnet.models import Assertion, Frame

from rdflib.Graph import Graph
from rdflib.store import Store
from rdflib import Namespace, Literal, BNode, RDF, plugin, URIRef

store = plugin.get('SQLite', Store)()
store.open('db')
g = Graph(store, identifier=URIRef(PREFIX+'graph/en'))

base = Namespace(PREFIX)
concept = Namespace(PREFIX+'concepts/')
reltype = Namespace(PREFIX+'reltypes/')
frame = Namespace(PREFIX+'frames/')
user = Namespace(PREFIX+'users/')
language = Namespace(PREFIX+'language/')


#surface_form_ = base['SurfaceForm']
left_text_ = base['LeftText']
right_text = base['RightText']

def b(thing): return base[thing]

class SuperNode(BNode):
    def __init__(self):
        g.add((self, RDF.type, RDF.Statement))

    def say(self, type, obj):
        g.add((self, type, obj))

def add(subj, type, obj):
    stmt = SuperNode()
    stmt.say(RDF.subject, subj)
    stmt.say(RDF.predicate, type)
    stmt.say(RDF.object, obj)
    return stmt

print 'Dumping assertions.'
for stem1, predtype, stem2, text1, text2, frame_id, language_id, creator_id, score, sentence in Assertion.useful.filter(language='en').values_list('stem1__text', 'predtype__name', 'stem2__text',
                                                                                                 'text1', 'text2', 'frame_id', 'language_id', 'creator_id', 'score', 'sentence__text').iterator():
    stmt = add(concept[stem1], reltype[predtype], concept[stem2])
    stmt.say(b('LeftText'), Literal(text1))
    stmt.say(b('RightText'), Literal(text2))
    stmt.say(b('FrameId'), frame[str(frame_id)])
    stmt.say(b('Language'), language[str(language_id)])
    stmt.say(b('Creator'), user[str(creator_id)])
    stmt.say(b('Score'), Literal(score))
    stmt.say(b('Sentence'), Literal(sentence))

g.commit()
print 'Dumping frames.'
for id, predtype, text, goodness in Frame.objects.filter(language='en').values_list('id', 'predtype__name', 'text', 'goodness').iterator():
    ff = frame[str(id)]
    g.add((ff, b('RelationType'), reltype[predtype]))
    g.add((ff, b('FrameText'), Literal(text)))
    g.add((ff, b('FrameGoodness'), Literal(str(goodness))))


g.commit()
