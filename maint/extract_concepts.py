#!/usr/bin/env python

from csc.conceptnet.models import Concept


from nltk import wordnet
def in_wordnet(word):
    base = wordnet.morphy(word)
    if base is None: base = word
    for d in wordnet.Dictionaries.values():
        if base in d: return True
        if word in d: return True
    return False


if __name__=='__main__':
    import sys
    lang = sys.argv[1]
    outfile = open(sys.argv[2], 'w')


    # Stopword detector
    from csc.representation.parsing.tools.models import FunctionFamily
    is_stopword = FunctionFamily.build_function_detector(lang, 'stop')

    import cPickle as pickle
    try:
        concepts = pickle.load(open('concepts_dict.pickle','rb'))
    except:
        concepts_qs = Concept.objects.filter(language=lang, num_predicates__gt=0)
        print >> sys.stderr, "Constructing concepts dictionary"
        concepts = dict(((c.text, c) for c in concepts_qs.iterator()))
        pickle.dump(concepts, open('concepts_dict.pickle','wb'), -1)

    print >> sys.stderr, "Filtering concepts"
    skipped1 = skipped2 = 0
    for stem_text, concept in concepts.iteritems():
        stem_words = stem_text.split(' ')
        if any(((word not in concepts) for word in stem_words)):
            print >> sys.stderr, "Skipped-1: "+ stem_text
            skipped1 += 1
            continue
        cname = concept.canonical_name
        if any(((not is_stopword(word) and not in_wordnet(word)) for word in cname.split(' '))):
            print >> sys.stderr, "Skipped-2: "+ stem_text
            skipped2 += 1
            continue
        print >> outfile, cname

    print "Skipped1: %d, Skipped2: %d, total: %d" % (skipped1, skipped2, len(concepts))
