from csc import divisi2
from csc.conceptnet.models import Assertion, Relation, RawAssertion, Feature
from csc.corpus.models import Language
from math import log, sqrt
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('csc.conceptnet.analogyspace2')

DEFAULT_IDENTITY_WEIGHT = 0
DEFAULT_CUTOFF = 5

log_2 = log(2)

def get_value(score, freq):
    """
    This function gives diminishing returns from higher scores, on a
    logarithmic scale. It also scales the resulting value according to the
    *frequency* value, which ranges from -10 to 10.
    """
    return (freq/10.0) * log(max((score+1, 1)))/log_2

### Getting quads of (concept1, relation, concept2, value) from the database.

def conceptnet_quads(query, cutoff=DEFAULT_CUTOFF):
    '''
    Generates a sequence of ((concept, relation, concept), value)
    triples for ConceptNet.
    
    Query can be a language identifier, in which case it will construct the
    default query for that language. It can also be a Django QuerySet
    containing Assertions, which it will use directly.
    '''
    if isinstance(query, (basestring, Language)):
        queryset = conceptnet_queryset(query, cutoff=cutoff)
    else:
        queryset = query

    for (relation, concept1, concept2, score, freq) in queryset.values_list(
        'relation__name', 'concept1__text', 'concept2__text', 'score', 'frequency__value').iterator():
        yield (concept1, relation, concept2, get_value(score, freq))

def conceptnet_queryset(lang=None, cutoff=DEFAULT_CUTOFF):
    """
    Construct a typical queryset for retrieving all relevant assertions
    from ConceptNet:

    - Limit it to a particular language, unless lang=None
    - Ensure that the reliability score is greater than 0
    - Use Assertion.useful to discard concepts that we have marked as invalid
    - Include only concepts that appear in a minimum number of assertions
      (the *cutoff*)
    """
    queryset = Assertion.useful.filter(score__gt=0)
    if lang is not None:
        queryset = queryset.filter(language=lang)
    if cutoff:
        queryset = queryset.filter(
            concept1__num_assertions__gte=cutoff,
            concept2__num_assertions__gte=cutoff)
    return queryset

def rating_quads(lang, cutoff=DEFAULT_CUTOFF, filter=None):
    '''
    Generates a quad for each rating (vote) on Assertions.

    A django.db.models.Q object passed to filter will be applied to
    the Vote queryset.
    '''
    from csc.conceptnet.models import AssertionVote
    ratings = AssertionVote.objects.filter(
        assertion__concept1__num_assertions__gte=cutoff,
        assertion__concept2__num_assertions__gte=cutoff)
    if filter is not None:
        ratings = ratings.filter(filter)
    for concept1, rel, concept2, vote in ratings.values_list(
        'assertion__concept1__text', 'assertion__relation__name', 'assertion__concept2__text', 'vote').iterator():
        yield (concept1, rel, concept2, vote)

def rawassertion_quads(lang, cutoff=DEFAULT_CUTOFF):
    # Experiment: deal with RawAssertions only.
    from csc.conceptnet4.models import RawAssertion
    queryset = RawAssertion.objects.filter(
        score__gt=0,
        surface1__concept__num_assertions__gte=cutoff,
        surface2__concept__num_assertions__gte=cutoff,
        language=lang)
    for (rel, concept1, concept2, text1, text2, frame_id, score, freq) in queryset.values_list(
        'frame__relation__name', 'surface1__concept__text',  'surface2__concept__text', 'surface1__text', 'surface2__text', 'frame__id', 'score', 'frame__frequency__value'
        ).iterator():
        value = get_value(score, freq)

        # Raw
        yield (text1, frame_id, text2, value)

        # Assertion
        yield (concept1, rel, concept2, value)

        ## NormalizesTo
        yield (concept1, 'NormalizesTo', text1, 1)
        yield (concept2, 'NormalizesTo', text2, 1)
        yield (concept1, 'NormalizesTo', concept1, 1)
        yield (concept2, 'NormalizesTo', concept2, 1)

def to_value_concept_feature(quads):
    """
    Convert a stream of assertion quads into a stream of twice
    as many (value, concept, feature) triples.
    """
    for concept1, rel, concept2, value in quads:
        yield value, concept1, ('right', rel, concept2)
        yield value, concept2, ('left', rel, concept1)

def to_value_concept_concept(quads):
    """
    Convert a stream of assertion quads into a stream of twice
    as many (value, concept1, concept2) triples, ignoring the relation and
    simply treating all kinds of edges equally.
    """
    for concept1, rel, concept2, value in quads:
        yield value, concept1, concept2
        yield value, concept2, concept1

def to_value_pair_relation(quads):
    """
    Convert a stream of assertion quads into a stream of
    (value, conceptPair, relation) triples.
    """
    for concept1, rel, concept2, value in quads:
        concept1, rel, concept2 = triple
        yield value, (concept1, concept2), rel

def build_matrix(query, cutoff=DEFAULT_CUTOFF, identity_weight=DEFAULT_IDENTITY_WEIGHT, data_source=conceptnet_quads, transform=to_value_concept_feature):
    """
    Builds a Divisi2 SparseMatrix from relational data.

    One required argument is the `query`, which can be a QuerySet or just a
    language identifier.

    Optional arguments:

    - `cutoff`: specifies how common a concept has to be to appear in the
      matrix. Defaults to DEFAULT_CUTOFF=5.
    - `identity_weight`
    - `data_source`: a function that produces (concept1, rel, concept2, value)
      quads given the `query` and `cutoff`. Defaults to
      :meth:`conceptnet_quads`.
    - `transform`: the function for transforming quads into
      (value, row_name, column_name) triples. Defaults to
      :meth:`to_value_concept_feature`, which yields
      (value, concept, feature) triples.
    """
    logger.info("Performing ConceptNet query")
    quads = list(data_source(query, cutoff))
    # todo: separate this out into a customizable function
    
    if identity_weight > 0:
        logger.info("Adding identities")
        morequads = []
        concept_set = set(q[0] for q in quads)
        for concept in concept_set:
            morequads.append( (concept, 'InheritsFrom', concept, identity_weight) )
        for c1, rel, c2, val in quads:
            if rel == 'IsA':
                morequads.append( (c1, 'InheritsFrom', c1, val) )
        quads.extend(morequads)

    logger.info("Creating triples")
    triples = transform(quads)
    logger.info("Building matrix")
    matrix = divisi2.make_sparse(triples)
    logger.info("Squishing underused rows")
    return matrix.squish(cutoff)

