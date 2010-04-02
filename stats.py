from conceptnet4.models import *
from operator import itemgetter

def relations_distribution(lang):
    return sorted(
        ((relation.name, relation.assertion_set.filter(language=lang).count())
         for relation in Relation.objects.filter(description__isnull=False)),
        key=itemgetter(1))

def sample_assertions(relation, n=10):
    return [assertion.nl_repr() for assertion in
            Relation.get(relation).assertion_set
            .filter(score__gt=0).order_by('?')[:n]]

def oldest_assertion(lang):
    return Assertion.objects.filter(language=lang).order_by('-rawassertion__created')[0]


if __name__ == '__main__':
    print relations_distribution('en')
    
        
