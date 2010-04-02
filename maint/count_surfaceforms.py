#!/usr/bin/env python

from csc.conceptnet4.models import SurfaceForm, RawAssertion
from csc.util import queryset_foreach
from django.db.models import Q

fixed = 0

def update_count(surface):
    global fixed
    num_raws = RawAssertion.objects.filter(Q(surface1=surface) | Q(surface2=surface)).count()
    if num_raws != surface.use_count:
        fixed += 1
        surface.use_count = num_raws
        surface.save()

def update_surfaceform_usecounts(lang):
    '''Fix the num_assertions count for each concept'''
    status = queryset_foreach(SurfaceForm.objects.filter(language=lang), update_count)
    print 'Updated counts on %d of %d surface forms' % (fixed, status.total)
    return status

if __name__=='__main__':
    import sys
    lang = sys.argv[1]
    status = update_surfaceform_usecounts(lang)
