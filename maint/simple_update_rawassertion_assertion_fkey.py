from csc.conceptnet.models import RawAssertion, Concept, Assertion
from django.db import transaction
import sys

no_assertion = set()
nonunique = set()

@transaction.commit_on_success
def main():
    updated_count = 0

    for raw in RawAssertion.objects.filter(predicate__id__isnull=True).iterator():
        assertions = list(Assertion.objects.filter(sentence__id=raw.sentence_id))
        if len(assertions) == 0:
            no_assertion.add(raw.id)
        elif len(assertions)==1:
            updated_count += 1
            if updated_count % 1000 == 1:
                sys.stderr.write('\r'+str(updated_count))
                sys.stderr.flush()
                transaction.commit_if_managed()
            raw.predicate = assertions[0]
            raw.save()
        else:
            nonunique.add(raw.id)

    print 'Updated', updated_count, 'assertions'
    print 'No assertion for', len(no_assertion), 'assertions'
    print 'Non-unique assertion for', len(nonunique), 'assertions'

if __name__ == '__main__':
    main()
