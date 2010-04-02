from csc.conceptnet4.models import RawAssertion, Concept, Assertion,\
SurfaceForm
from django.db import transaction

people = Concept.get('people', 'en')
person = Concept.get('person', 'en')

@transaction.commit_on_success
def fix_all():
    for peopleform in people.surfaceform_set.all():
        print peopleform
        peopleform.concept = person
        peopleform.save()
        for raw in RawAssertion.objects.filter(surface1=peopleform):
            print raw.update_assertion()
        for raw in RawAssertion.objects.filter(surface2=peopleform):
            print raw.update_assertion()

if __name__ == '__main__': fix_all()

