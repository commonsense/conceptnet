from csc.conceptnet.models import RawAssertion, Concept, Assertion
from django.db import transaction

no_assertion = set()
nonunique = set()
failed = set()

@transaction.commit_on_success
def main():
    updated_count = 0
    for raw in RawAssertion.objects.filter(predicate__id__isnull=True)[:1000].iterator():
        try:
            concept1 = Concept.get(raw.text1, raw.language_id)
            concept2 = Concept.get(raw.text2, raw.language_id)
            assertions = list(Assertion.objects.filter(stem1=concept1,
                                                       stem2=concept2,
                                                       predtype__id=raw.predtype_id))
            if len(assertions) == 0:
                no_assertion.add(raw.id)
            elif len(assertions) == 1:
                updated_count += 1
                raw.predicate = assertions[0]
                raw.save()
            else:
                nonunique.add(raw.id)
        except:
            failed.add(raw.id)

    print 'Updated', updated_count, 'assertions'
    print 'No assertion for', len(no_assertion), 'assertions'
    print 'Non-unique assertion for', len(nonunique), 'assertions'
    print len(failed), 'failed.'

if __name__ == '__main__':
    main()
