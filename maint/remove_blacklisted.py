from csc.conceptnet.models import *

for concept in Concept.objects.all():
    if concept.language.nl.is_blacklisted(concept.text):
        concept.useful = False
        concept.save()
