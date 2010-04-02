#!/usr/bin/env python

from csc.conceptnet4.models import Concept
from csc.util import queryset_foreach

concepts_fixed = 0
significant = 0

def fix_concept(concept):
    global concepts_fixed, significant
    rels = concept.get_assertions(useful_only=True).count()
    if rels != concept.num_assertions:
        # print '%s: %d->%d' % (concept.canonical_name, concept.num_assertions, rels)
        concepts_fixed += 1
        if rels > 2:
            significant += 1
        concept.num_assertions = rels
        concept.save()
    if not concept.words:
        concept.words = len(concept.text.split())
        concept.save()

def update_assertion_counts(lang):
    '''Fix the num_assertions count for each concept'''
    status = queryset_foreach(Concept.objects.filter(language=lang), fix_concept)
    print 'Fixed %s of %s concepts (%s with >2 rels).' % (concepts_fixed, status.total, significant)
    return status

if __name__=='__main__':
    import sys
    lang = sys.argv[1]
    status = update_assertion_counts(lang)
