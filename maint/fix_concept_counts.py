#!/usr/bin/env python

'''
Concepts keep track of their number of words. Or, they should.
'''

from csc.util.batch import queryset_foreach
from csc.conceptnet4.models import Concept
from django.db.models.query import Q

def fix_concept_counts():
    def fix_concept(concept):
        if concept.words: return
        concept.words = len(concept.text.split())
        concept.save()

    return queryset_foreach(
        Concept.objects.filter(Q(words=0) | Q(words__isnull=True)), fix_concept)

if __name__ == '__main__':
    fix_concept_counts()
