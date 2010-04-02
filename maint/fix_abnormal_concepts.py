from csc.util import queryset_foreach
from csc.conceptnet.models import Concept, SurfaceForm, Language, Assertion
from django.db import connection

en = Language.get('en')

def fix_surface(surface):
    norm, residue = en.nl.lemma_split(surface.text)
    if norm != surface.concept.text:
        print
        print "surface:", surface.text.encode('utf-8')
        print "concept:", surface.concept.text.encode('utf-8')
        print "normal:", norm.encode('utf-8')
        surface.update(norm, residue)

queryset_foreach(SurfaceForm.objects.filter(language=en),
  fix_surface,
  batch_size=100)


# plan:
#  fix surface form -> concept mapping
#  remove obsolete concepts
