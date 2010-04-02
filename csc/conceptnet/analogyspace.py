from csc.divisi.tensor import DictTensor
from csc.divisi.labeled_view import LabeledView
from csc.divisi.ordered_set import OrderedSet
from csc.divisi.blend import Blend
from csc.conceptnet.models import Assertion, Relation, RawAssertion
from csc.corpus.models import Language
from math import log, sqrt
import logging

DEFAULT_IDENTITY_WEIGHT = sqrt(5)
DEFAULT_CUTOFF = 5

log_2 = log(2)

###
### General utilities
###

relation_name_cache = None
def get_relation_names():
    global relation_name_cache
    if relation_name_cache is None:
        relation_name_cache = dict((x.id, x.name)
                                   for x in Relation.objects.all())
    return relation_name_cache

def get_value(score, freq):
    return freq * log(max((score+1, 1)))/log_2 / 10.0

###
### Getting triples from the database.
###

def conceptnet_triples(lang, cutoff=DEFAULT_CUTOFF, value_for_score_and_freq=get_value, extra_filters=None):
    '''
    Generates a sequence of ((concept, relation, concept), value)
    triples for ConceptNet in the given language.

    You can pass a queryset instead of `lang`, and it will be used,
    ignoring cutoffs. It should be a queryset of Assertions.

    You can pass in a django.db.models.Q object for extra_filters, and
    it will get applied to the Assertion queryset.
    '''
    if isinstance(lang, (basestring, Language)):
        queryset = conceptnet_queryset(lang, cutoff=cutoff)
    else:
        queryset = lang

    if extra_filters is not None:
        queryset = queryset.filter(extra_filters)

    for (relation, concept1, concept2, score, freq) in queryset.values_list(
        'relation__name', 'concept1__text', 'concept2__text', 'score', 'frequency__value').iterator():
        yield (concept1, relation, concept2), value_for_score_and_freq(score, freq)

def conceptnet_queryset(lang=None, cutoff=DEFAULT_CUTOFF):
    queryset = Assertion.useful.filter(score__gt=0)
    if cutoff:
        queryset = queryset.filter(
            concept1__num_assertions__gt=cutoff,
            concept2__num_assertions__gt=cutoff)
    if lang is not None:
        queryset = queryset.filter(language=lang)
    return queryset

def rating_triples(lang, cutoff=DEFAULT_CUTOFF, filter=None):
    '''
    Generates a triple for each rating (vote) on Assertions.

    A django.db.models.Q object passed to filter will be applied to
    the Vote queryset.
    '''
    from csc.conceptnet.models import AssertionVote
    ratings = AssertionVote.objects.filter(
        assertion__concept1__num_assertions__gt=cutoff,
        assertion__concept2__num_assertions__gt=cutoff)
    if filter is not None:
        ratings = ratings.filter(filter)
    for concept1, rel, concept2, vote in ratings.values_list(
        'assertion__concept1__text', 'assertion__relation__name', 'assertion__concept2__text', 'vote').iterator():
        yield (concept1, rel, concept2), vote

def rawassertion_triples(lang, cutoff=DEFAULT_CUTOFF, value_for_score_and_freq=get_value):
    from csc.conceptnet4.models import RawAssertion
    queryset = RawAssertion.objects.filter(
        score__gt=0 ,
        surface1__concept__num_assertions__gt=cutoff,
        surface2__concept__num_assertions__gt=cutoff,
        language=lang)
    for (rel, concept1, concept2, text1, text2, frame_id, score, freq) in queryset.values_list(
        'frame__relation__name', 'surface1__concept__text',  'surface2__concept__text', 'surface1__text', 'surface2__text', 'frame__id', 'score', 'frame__frequency__value'
        ).iterator():
        value = value_for_score_and_freq(score, freq)

        # Raw
        yield (text1, frame_id, text2), value

        # Assertion
        yield (concept1, rel, concept2), value

        ## NormalizesTo
        #yield (concept1, 'NormalizesTo', text1), 1
        #yield (concept2, 'NormalizesTo', text2), 1
        #yield (concept1, 'NormalizesTo', concept1), 1
        #yield (concept2, 'NormalizesTo', concept2), 1

###
### Building AnalogySpace
###

class ConceptNet2DTensor(LabeledView):
    def __init__(self):
        super(ConceptNet2DTensor, self).__init__(
            DictTensor(2), [OrderedSet() for _ in '01'])

    def add_assertion(self, relation, left, right, value):
        # FIXME: doesn't actually add. Need to evaluate the impact of that before changing.
        lfeature = ('left',relation,left)
        rfeature = ('right',relation,right)
        self[left, rfeature] = value
        self[right, lfeature] = value

    def add_identity_assertion(self, relation, text, value):
        self.add_assertion(relation, text, text, value)

    def to_labeled_view(self):
        return LabeledView(self.tensor, self._labels)


class ConceptNet3DTensor(LabeledView):
    def __init__(self):
        concepts, relations = OrderedSet(), OrderedSet()
        super(ConceptNet3DTensor, self).__init__(
            DictTensor(3), [concepts, relations, concepts])

    def add_assertion(self, relation, left, right, value):
        self[left, relation, right] += value

    def add_identity_assertion(self, relation, text, value):
        self[text, relation, text] += value


class MirroringCNet3DTensor(ConceptNet3DTensor):
    '''
    Every assertion (c1, r, c2) in this tensor has an inverse,
    (c2, r', c1).

    This is analogous to how the 2D tensor makes left and right features.

    Inverse relations are constructed from ordinary relations by
    prefixing a '-'.
    '''
    def add_assertion(self, relation, left, right, value):
        self[left, relation, right] += value # normal
        self[right, '-'+relation, left] += value # inverse
        
    
    
class AnalogySpaceBuilder(object):
    @classmethod
    def build(cls, **kw):
        return cls(**kw)()

    def __init__(self,
                 identity_weight=DEFAULT_IDENTITY_WEIGHT,
                 identity_relation=u'InheritsFrom',
                 cutoff=DEFAULT_CUTOFF,
                 tensor_class=ConceptNet2DTensor):
        self.identity_weight = identity_weight
        self.identity_relation = identity_relation
        self.cutoff = cutoff
        self.tensor_class = tensor_class

    def __call__(self):
        '''Builds a ConceptNet tensor from the database.'''
        tensor = self.queryset_to_tensor(self.queryset())
        self.add_identities(tensor)
        return tensor
    
    def queryset(self):
        return Assertion.useful.filter(
            score__gt=0,
            concept1__num_assertions__gt=self.cutoff,
            concept2__num_assertions__gt=self.cutoff)

    @staticmethod
    def get_value(score, freq):
        return freq * log(max((score+1, 1)))/log_2 / 10.0

    def queryset_to_tensor(self, queryset):
        '''Returns the tensor (without identities) built from the
        assertions in the given queryset.'''
        tensor = self.tensor_class()
        addToTensor = tensor.add_assertion
        get_value = self.get_value
        for (relation, concept1, concept2, score, freq) in queryset.values_list(
            'relation__name', 'concept1__text',  'concept2__text',  'score',
            'frequency__value').iterator():
            value = get_value(score, freq)
            addToTensor(relation, concept1, concept2, value)
        return tensor

    def add_identities(self, tensor):
        weight = self.identity_weight
        if weight == 0:
            logging.info('Skipping adding zero-weight identities.')
            return

        rel = self.identity_relation
        add_identity_assertion = tensor.add_identity_assertion
        logging.info('Adding identities, weight=%s', weight)
        for text in list(tensor.label_list(0)):
            add_identity_assertion(rel, text, weight)


class MonolingualAnalogySpaceBuilder(AnalogySpaceBuilder):
    @classmethod
    def build(cls, lang, **kw):
        return cls(lang=lang, **kw)()

    
    def __init__(self, lang, **kw):
        super(MonolingualAnalogySpaceBuilder, self).__init__(**kw)
        self.lang = lang

    
    def queryset(self):
        return super(MonolingualAnalogySpaceBuilder, self).queryset().filter(language=self.lang)
    
            
# Experiment: an AnalogySpace from frames
class FramedTensorBuilder(MonolingualAnalogySpaceBuilder):
    def queryset(self):
        return RawAssertion.objects.filter(
            score__gt=0,
            assertion__concept1__num_assertions__gt=self.cutoff,
            assertion__concept2__num_assertions__gt=self.cutoff,
            language=self.lang)

    def queryset_to_tensor(self, queryset):
        tensor = self.tensor_class()
        add_assertion = tensor.add_assertion
        get_value = self.get_value

        for (rel, concept1, concept2, text1, text2, frame_id, score) in queryset.values_list(
            'assertion__relation__name', 'assertion__concept1__text',  'assertion__concept2__text', 'surface1__text', 'surface2__text', 'frame_id', 'score'
            ).iterator():
            value = get_value(score, 5)
            # Raw
            add_assertion(frame_id, text1, text2, value)
            # Assertion
            add_assertion(rel, concept1, concept2, value)
            # NormalizesTo
            add_assertion('NormalizesTo', text1, concept1, 1)
            add_assertion('NormalizesTo', text2, concept2, 1)
            add_assertion('NormalizesTo', concept1, concept1, 1)
            add_assertion('NormalizesTo', concept2, concept2, 1)
        return tensor


# Experiment: Multilingual AnalogySpace
class MultilingualAnalogySpaceBuilder(AnalogySpaceBuilder):
    def queryset_to_tensor(self, queryset):
        tensor = self.tensor_class()
        add_assertion = tensor.add_assertion
        get_value = self.get_value

        relation_name = get_relation_names()
        for (rel_id, name1, name2, score, freq, lang) in queryset.values_list(
            'relation_id', 'concept1__text',  'concept2__text',  'score', 'frequency__value', 'language_id').iterator():

            value = get_value(score, freq)
            relation = relation_name[rel_id]
            lconcept = (name1, lang)
            rconcept = (name2, lang)
            add_assertion(relation, lconcept, rconcept, value)
        return tensor


# Experiment: One relation type at a time
class ByRelationBuilder(MonolingualAnalogySpaceBuilder):
    def queryset_for_relation(self, relation_id):
        '''Returns a QuerySet of just the assertions having the
        specified relation.'''
        return self.queryset().filter(relation__id=relation_id)

    def tensor_for_relation(self, relation_id):
        '''Returns a tensor built only from assertions of the given relation.'''
        return self.queryset_to_tensor(self.queryset_for_relation(relation_id))

    def get_tensors_by_relation(self):
        '''Returns a dictionary mapping names of relations to tensors of that kind of data.'''
        relation_name = get_relation_names()
        by_rel = [(relation_name[rel_id], self.tensor_for_relation(rel_id))
                  for rel_id in relation_name.keys()
                  if relation_name[rel_id] != 'InheritsFrom']
        return dict((name, tensor) for (name, tensor) in by_rel
                    if len(tensor) > 0)

    def identities_for_all_relations(self, byrel):
        '''Returns a tensor containing identity relations for the
        concepts in all tensors. We handle this separately so the
        blends don't include identities.'''
        # Build a tensor with all the concept labels.
        tensor = self.tensor_class()
        for other in byrel.itervalues():
            tensor._labels[0].extend(other._labels[0])
        # Add identities to that as normal.
        self.add_identities(tensor)
        return tensor

    def __call__(self):
        byrel = self.get_tensors_by_relation()
        identity_tensor = self.identities_for_all_relations(byrel)
        return Blend(byrel.values() + [identity_tensor])

# A backwards-compatibility method.
def load_one_type(lang, relation, identities, cutoff):
    return ByRelationBuilder(lang, identity_weight=identities, cutoff=cutoff).tensor_for_relation(relation)

def conceptnet_by_relations(lang, **kw):
    return ByRelationBuilder(lang, **kw).get_tensors_by_relation()

# Experiment: Flatten (just by weighted concepts)
class FlatConceptNetTensor(LabeledView):
    def __init__(self):
        concepts = OrderedSet()
        super(ConceptNet2DTensor, self).__init__(DictTensor(2), [concepts, concepts])

class FlatASpaceBuilder(MonolingualAnalogySpaceBuilder):
    def __init__(self, forward_weight_by_relation, forward_default_weight,
                 inverse_weight_by_relation, inverse_default_weight,
                 min_identity_weight=0.0, tensor_class=FlatConceptNetTensor, **kw):
        super(FlatASpaceBuilder, self).__init__(tensor_class=tensor_class, **kw)
        self.get_forward_weight = lambda relation: forward_weight_by_relation.get(relation, forward_default_weight)
        self.get_inverse_weight = lambda relation: inverse_weight_by_relation.get(relation, inverse_default_weight)
        self.min_identity_weight = min_identity_weight

    def queryset_to_tensor(self, queryset):
        tensor = self.tensor_class()
        ## Micro-optimization:
        #tensor._labels[1] = tensor._labels[0]
        get_forward_weight = self.get_forward_weight
        get_inverse_weight = self.get_inverse_weight
        get_value = self.get_value

        for (relation, concept1, concept2, score, freq) in queryset.values_list(
            'relation__name', 'concept1__text',  'concept2__text',  'score',
            'frequency__value').iterator():

            value = get_value(score, freq)
            # Add the forward link
            fwd_val = get_forward_weight(relation)
            if fwd_val: tensor[concept1, concept2] += fwd_val * value
            # Add the reverse link
            rev_val = get_inverse_weight(relation)
            if rev_val: tensor[concept2, concept1] += rev_val * value
        return tensor

    def add_identities(self, tensor):
        min_identity_weight = self.min_identity_weight
        if min_identity_weight:
            # Ensure that the minimum weight of any concept with itself is min_identity_weight
            for concept in tensor.label_list(0):
                if tensor[concept, concept] < min_identity_weight:
                    tensor[concept, concept] = min_identity_weight
    


# Compatibility API
def rename_elt(dct, old, new):
    if old in dct:
        dct[new] = dct[old]
        del dct[old]
        
def conceptnet_2d_from_db(lang, builder=MonolingualAnalogySpaceBuilder, **kw):
    '''Build a ConceptNet tensor in the given language.'''
    # Handle an old parameter
    rename_elt(kw, 'identities', 'identity_weight')
    return builder(lang=lang, **kw)().to_labeled_view()


def conceptnet_selfblend(lang, **kw):
    return conceptnet_2d_from_db(lang, builder=ByRelationBuilder, **kw)


### Experiment: Add cooccurrences
class ConceptNetTensorWithCooccurrences(ConceptNet2DTensor):
    @classmethod
    def get_constructor(cls, cooccurrence_weight):
        def constructor():
            return cls(cooccurrence_weight)
        return constructor


    def __init__(self, cooccurrence_weight, *a, **kw):
        super(ConceptNet2DTensor, self).__init__(*a, **kw)
        self.cooccurrence_weight = cooccurrence_weight
        
    def add_assertion(self, relation, left, right, value):
        # Add the normal assertion.
        super_add_assertion = super(ConceptNetTensorWithCooccurrences, self)
        super_add_assertion.add_assertion(relation, left, right, value)
    
        # Split apart right-side concepts.
        rel = 'CooccursWith'
        for right_side_word in right.split():
            super_add_assertion(rel, left, right_side_word, value)

def conceptnet_2d_with_cooccurrences(lang, cooccurrence_weight=1.0, **kw):
    kw['tensor_class'] = ConceptNetTensorWithCooccurrences.get_constructor(cooccurrence_weight)
    return conceptnet_2d_from_db(lang, **kw)

###
### Analysis helpers
###

def concept_similarity(svd, concept):
    return svd.u_dotproducts_with(svd.weighted_u_vec(concept))

def predict_features(svd, concept):
    return svd.v_dotproducts_with(svd.weighted_u_vec(concept))

def feature_similarity(svd, feature):
    return svd.v_dotproducts_with(svd.weighted_v_vec(feature))

def predict_concepts(svd, feature):
    return svd.u_dotproducts_with(svd.weighted_v_vec(feature))

def make_category(svd, concepts=[], features=[]):
    from operator import add
    ulabels = svd.u.label_list(0)
    vlabels = svd.v.label_list(0)
    components = (
        [svd.weighted_u_vec(concept) for concept in concepts if concept in ulabels] +
        [svd.weighted_v_vec(feature) for feature in features if feature in vlabels])
    if len(components) == 0:
        raise KeyError("None of the given concepts or features are in the matrix")
    return reduce(add, components)


def category_similarity(svd, cat):
    '''Return all the features and concepts that are close to the given
    category, as (concepts, features), both labeled dense tensors.

    Example usage:
    concepts, features = category_similarity(svd, cat)
    concepts.top_items(10)
    features.top_items(10)'''
    return svd.u_dotproducts_with(cat), svd.v_dotproducts_with(cat)

def eval_assertion(svd, relation, left, right):
    lfeature = ('left',relation,left)
    rfeature = ('right',relation,right)

    # Evaluate right feature
    try:
        rfeature_val = svd.get_ahat((left, rfeature))
    except KeyError:
        rfeature_val = 0

    # Evaluate left feature
    try:
        lfeature_val = svd.get_ahat((right, lfeature))
    except KeyError:
        lfeature_val = 0

    return lfeature_val, rfeature_val


