from csc.util import queryset_foreach
from csc.conceptnet.models import Concept, Language

def set_visible(concept):
    if not concept.language.nl.is_blacklisted(concept.text):
        concept.visible=True
        concept.save()

def set_invisible(concept):
    if concept.language.nl.is_blacklisted(concept.text):
        concept.visible=False
        concept.save()
        
queryset_foreach(Concept.objects.filter(visible=False), set_visible)

