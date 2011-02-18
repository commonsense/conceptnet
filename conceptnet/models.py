__version__ = "4.0rc2"
from django.db import models
from django.db.models import Q
from csc.corpus.models import Language, Sentence, User, ScoredModel, Frequency
from events.models import Event, Activity
from voting.models import Vote, SCORES
from django.contrib.contenttypes import generic
from csc.util import cached
from datetime import datetime
from urllib import quote as urlquote
import re

DEFAULT_LANGUAGE = en = Language(id='en', name='English') 

class TimestampedModel(models.Model):
    created = models.DateTimeField(default=datetime.now)
    updated = models.DateTimeField()
    
    def save(self, **kwargs):
        self.updated = datetime.now()
        super(TimestampedModel, self).save(**kwargs)

    class Meta:
        abstract = True

class UserData(TimestampedModel):
    user = models.ForeignKey(User)
    activity = models.ForeignKey(Activity)
    
    class Meta:
        abstract = True

class Batch(TimestampedModel):
    owner = models.ForeignKey(User)
    status = models.CharField(max_length=255,blank=True)
    remarks = models.TextField(blank=True)
    progress_num = models.IntegerField(default=0)
    progress_den = models.IntegerField(default=0)

    def __unicode__(self):
        return u"Batch " + str(self.id) + " (owner: " + self.owner.username + ") <" + str(self.progress_num) + "/" + str(self.progress_den) + " " + self.status + ">"


class Relation(models.Model):
    name = models.CharField(max_length=128,unique=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    def __unicode__(self):
        return self.name

    @classmethod
    def get(cls, name):
        # Check if the parameter is already a Relation. We don't use
        # isinstance in case of accidental multiple imports (e.g.,
        # csc.conceptnet4.models vs conceptnet4.models).
        if hasattr(name, 'id'):
            return name
        return cls.objects.get(name=name)

class Frame(models.Model):
    """
    A Frame is a natural-language template containing two slots, representing a
    way that a :class:`Relation` could be expressed in language.
    
    It can be used
    for pattern matching to create a :class:`RawAssertion`, or to express an
    existing :class:`RawAssertion` as a sentence.
    """
    language = models.ForeignKey(Language)
    text = models.TextField()
    relation = models.ForeignKey(Relation)
    goodness = models.IntegerField()
    frequency = models.ForeignKey(Frequency)
    question_yn = models.TextField(null=True, blank=True)
    question1 = models.TextField(null=True, blank=True)
    question2 = models.TextField(null=True, blank=True)

    def preferred(self):
        return self.goodness > 2
    preferred.boolean = True
    
    def fill_in(self, a, b):
        """
        Fill in the slots of this frame with the strings *a* and *b*.
        """
        res = self.text.replace('{%}', '')
        res = res.replace('{1}', a, 1)
        return res.replace('{2}', b, 1)

    def __unicode__(self):
        return "%s (%s)" % (self.text, self.language.id)
    def re_pattern(self):
        if not hasattr(self, '_re_pattern'):
            self._re_pattern = re.compile(self.text.replace('{%}',
            '').replace('{1}', '(.+)').replace('{2}', '(.+)').strip('. '))
        return self._re_pattern
    def match(self, text):
        match = self.re_pattern().match(text)
        if match:
            return match.groups()
        else: return None
    def display(self):
        return self.fill_in('...', '...')
    
    @staticmethod
    def match_sentence(text, language):
        text = text.strip('. ')
        for frame in Frame.objects.filter(language=language,
        goodness__gte=2).order_by('-goodness'):
            result = frame.match(text)
            if result:
                return frame, result
        return None


class Feature(object):
    """
    Features are not models in the database, but they are useful ways to
    describe the knowledge contained in the edges of ConceptNet.

    A Feature is the combination of a :class:`Concept` and a :class:`Relation`.
    The combination of a Concept and a Feature, then, gives a
    :class:`Proposition`, a statement that can have a truth value; when given a
    truth value, this forms an :class:`Assertion`.

    As an example, the relation ``PartOf(cello, orchestra)`` breaks down into
    the concept ``cello`` and the feature ``PartOf(x, orchestra)``. It also
    breaks down into ``orchestra`` and ``PartOf(cello, x)``.

    Features can be *left features* or *right features*, depending on whether
    they include the left or right concept (that is, the first or second
    argument) in the Assertion. The Feature class itself is an abstract class,
    which is realized in the classes :class:`LeftFeature` and
    :class:`RightFeature`.
    
    Each Assertion can be described with its
    left concept (:attr:`concept1`) and its right feature, or its right concept
    (:attr:`concept2`) and its left feature.

    The notation is based on putting the relation in a "bucket". For
    example, ``PartOf(cello, orchestra) =
    cello\PartOf/orchestra``. Breaking this apart gives left and right
    features::

      cello: PartOf/orchestra (left concept and right feature)
      orchestra: cello\PartOf (right concept and left feature)
      
    """
    
    def __init__(self, relation, concept):
        """
        Create a LeftFeature or RightFeature (depending on which class you
        instantiate), with the given relation and concept.
        """
        if self.__class__ == Feature:
            raise NotImplementedError("Feature is an abstract class")
        if isinstance(relation, basestring):
            relation = Relation.objects.get(name=relation)
        #if isinstance(concept, basestring):
        #    concept = Concept.get(concept, auto_create=True)
        self.relation = relation
        self.concept = concept
        
    def to_tuple(self):
        return (self.tuple_key, self.relation.name, self.concept.text)
    @property
    def language(self):
        return self.concept.language
    def __hash__(self): # Features should be immutable.
        return hash((self.__class__.__name__, self.relation, self.concept))
    def __cmp__(self, other):
        if not isinstance(other, Feature): return -1
        return cmp((self.__class__, self.relation, self.concept),
                   (other.__class__, other.relation, other.concept))
    @staticmethod
    def from_tuple(tup, lang=DEFAULT_LANGUAGE, lemmatize=False):
        """
        Some systems such as AnalogySpace use a lower-level representation of
        features, representing them as a tuple of three strings:
        ``(left_or_right, relation, concept)``. This factory method takes in
        such a tuple and produces a proper Feature object.
        """
        typ, rel, txt = tup
        if lemmatize:
            c = Concept.get(txt, lang)
        else:
            c, _ = Concept.objects.get_or_create(text=txt, language=lang)
        r = Relation.objects.get(name=rel)
        return Feature.from_obj_tuple(typ, r, c)
    @staticmethod
    def from_obj_tuple(typ, relation, concept):
        classes = {'left': LeftFeature, 'right': RightFeature}
        if typ not in classes: raise ValueError
        return classes[typ](relation, concept)
        
    @property
    def frame(self):
        """
        Get a good natural-language frame for expressing this feature. For
        backward compatibility, this is a property.
        """
        return Frame.objects.filter(language=self.language,
                                    relation=self.relation).order_by('-goodness')[0]
    def fill_in(self, newconcept):
        """
        Fill in the blank of this feature with a :class:`Concept`. The result
        is a :class:`Proposition`.
        """
        raise NotImplementedError, "Feature is an abstract class"
    def matching_assertions(self):
        """
        Get all :class:`Assertions` that contain this feature.
        """
        raise NotImplementedError, "Feature is an abstract class"
    def matching_raw(self):
        """
        Get all :class:`RawAssertions` that contain this feature.
        """
        raise NotImplementedError, "Feature is an abstract class"
    def nl_frame(self, gap=None):
        """
        This code is kinda confused.
        """
        examples = self.matching_raw().filter(frame__frequency__value__gt=0, frame__goodness__gte=3)
        try:
            return examples[0].frame
        except IndexError:
            examples = self.matching_raw().filter(frame__frequency__value__gt=0, frame__goodness__gte=2)
            try:
                return examples[0].frame
            except IndexError:
                # If we can't find an example, just get the best frame
                return Frame.objects.filter(
                    language=self.language,
                    relation=self.relation,
                    frequency__value__gt=0
                ).order_by('-goodness')[0]

    def nl_statement(self, gap='...'):
        """
        Express this feature as a statement in natural language. The omitted
        concept is replaced by the value in *gap*.
        """
        frame, ftext, text1, text2 = self.nl_parts(gap)
        return frame.fill_in(text1, text2)
    def _matching_assertions(self):
        return Assertion.objects.filter(
          language=self.concept.language,
          score__gt=0,
          relation=self.relation)
    def _matching_raw(self):
        return RawAssertion.objects.filter(
          language=self.concept.language,
          assertion__relation=self.relation)
        
    @cached(lambda self, gap: 'nl_parts_'+unicode(self)+'_'+gap, cached.day)
    def nl_parts(self, gap='...'):
        """
        Get a 4-tuple, ``(frame, ftext, text1, text2)``, that contains the
        information needed to express this feature in natural language:

        - The Frame object that is best for expressing this feature.
        - The text of that frame.
        - The text that fills the first blank in the frame (which might be
          :param:`gap`).
        - The text that fills the second blank in the frame (which might be
          :param:`gap`).
        """
        frame = self.nl_frame()
        matching_raw = self.matching_raw()
        try:
            surface = matching_raw[0].surface(self.idx)
        except IndexError:
            surface = self.concept.some_surface() or self.concept
        if isinstance(self, LeftFeature):
            return (frame, frame.text.replace('{%}', ''), surface.text, gap)
        elif isinstance(self, RightFeature):
            return (frame, frame.text.replace('{%}', ''), gap, surface.text)
    
    @property
    def direction(self):
        return self.tuple_key
    
    def __repr__(self):
        return "<Feature: %s>" % unicode(self)
    
class LeftFeature(Feature):
    idx = 1
    tuple_key = 'left'
    def __unicode__(self):
        return '%s\\%s' % (self.concept.text, self.relation)
    def fill_in(self, newconcept):
        return Proposition(self.concept, self.relation, newconcept, self.concept.language)
    def matching_assertions(self):
        return self._matching_assertions().filter(concept1=self.concept)
    def matching_raw(self):
        return self._matching_raw().filter(surface1__concept=self.concept)

class RightFeature(Feature):
    idx = 2
    tuple_key = 'right'
    def __unicode__(self):
        return '%s/%s' % (self.relation, self.concept.text)
    def fill_in(self, newconcept):
        return Proposition(newconcept, self.relation, self.concept, self.concept.language)
    def matching_assertions(self):
        return self._matching_assertions().filter(concept2=self.concept)
    def matching_raw(self):
        return self._matching_raw().filter(assertion__concept2=self.concept)

def ensure_concept(concept):
    if isinstance(concept, Concept): return concept
    lang = DEFAULT_LANGUAGE
    if isinstance(concept, (tuple, list)):
        text, lang = concept
    else:
        text = concept
    return Concept.get(text, lang, auto_create=True)
    
class Proposition(object):
    """
    A Proposition represents a statement that may or may not be true. It is
    like an :class:`Assertion` without a truth value.
    """
    def __init__(self, concept1, rel, concept2, lang):
        self.concept1 = ensure_concept(concept1)
        self.relation = rel
        self.concept2 = ensure_concept(concept2)
        self.lang = lang
    def __unicode__(self):
        return '<Proposition: %s %s %s>' % (self.concept1, self.relation,
        self.concept2)
    def nl_question_bad(self):
        """
        Express this Proposition as a question in natural language, poorly.
        """
        frame = Frame.objects.filter(language=self.lang, relation=self.relation,
                                     goodness__gte=3)[0]
        same_c1 = RawAssertion.objects.filter(language=self.lang,
            frame__relation=self.relation, surface1__concept=self.concept1)
        try:
            surface1 = same_c1[0].surface1.text
        except IndexError:
            surface1 = self.concept1.some_surface() or self.concept1
            surface1 = surface1.text
        same_c2 = RawAssertion.objects.filter(language=self.lang,
            frame__relation=self.relation, surface2__concept=self.concept2)
        try:
            surface2 = same_c2[0].surface2.text
        except IndexError:
            surface2 = self.concept2.some_surface() or self.concept2
            surface2 = surface2.text
        # The wiki-like brackets should be replaced by appropriate formatting.
        surface1b = "[[%s]]" % surface1
        surface2b = "[[%s]]" % surface2

        if frame.question_yn:
            return frame.question_yn.replace('{1}', surface1b)\
                   .replace('{2}', surface2b)
        else:
            return frame.text.replace('{1}', surface1b)\
                   .replace('{2}', surface2b)\
                   .replace('{%}', '') + '?'
    def right_feature(self):
        return RightFeature(self.relation, self.concept2)
    def left_feature(self):
        return LeftFeature(self.relation, self.concept1)
    def nl_parts(self):
        """
        Get a 4-tuple, ``(frame, ftext, text1, text2)``, that contains the
        information needed to express this feature in natural language:

        - The Frame object that is best for expressing this feature.
        - The text of that frame.
        - The text that fills the first blank in the frame.
        - The text that fills the second blank in the frame.
        """
        # TODO: replace this with something cleverer but still sufficiently
        # fast
        try:
            frame = Frame.objects.filter(language=self.lang,
            relation=self.relation, goodness__gte=3)[0]
        except IndexError:
            frame = Frame.objects.filter(language=self.lang,
            relation=self.relation).order_by('-goodness')[0]

        #frame = self.right_feature().nl_frame()
        #surfaces = {}
        same_c1 = RawAssertion.objects.filter(frame__relation=self.relation,
                                              surface1__concept=self.concept1)
        try:
            surface1 = same_c1[0].surface1.text
        except IndexError:
            surface1 = self.concept1.some_surface() or self.concept1
            surface1 = surface1.text
        same_c2 = RawAssertion.objects.filter(language=self.lang,
            frame__relation=self.relation, surface2__concept=self.concept2)            
        try:
            surface2 = same_c2[0].surface2.text
        except IndexError:
            surface2 = self.concept2.some_surface() or self.concept2
            surface2 = surface2.text
        return (frame, frame.text, surface1, surface2)
        
    def nl_parts_topdown(self):
        frame = Frame.objects.filter(language=self.lang,
        relation=self.relation, goodness__gte=3)[0]
        #surfaces = {}
        same_c1 = RawAssertion.objects.filter(language=self.lang,
            frame__relation=self.relation, surface1__concept=self.concept1)
        try:
            surface1 = same_c1[0].surface1.text
        except IndexError:
            surface1 = self.concept1.some_surface() or self.concept1
            surface1 = surface1.text
        same_c2 = RawAssertion.objects.filter(language=self.lang,
            frame__relation=self.relation, surface2__concept=self.concept2)            
        try:
            surface2 = same_c2[0].surface2.text
        except IndexError:
            surface2 = self.concept2.some_surface() or self.concept2
            surface2 = surface2.text
        return (frame, frame.text, surface1, surface2)

class Concept(models.Model):
    """
    Concepts are the nodes of ConceptNet. They are the things that people have
    common sense knowledge about.
    
    Concepts are expressed in natural language with
    sets of related words and phrases: for example, "take a picture", "taking
    pictures", "to take pictures", and "you take a picture" are various
    `surface forms`_ of the same Concept.
    """
    language = models.ForeignKey(Language)
    text = models.TextField(db_index=True)
    num_assertions = models.IntegerField(default=0)
    # canonical_name = models.TextField()
    words = models.IntegerField()
    visible = models.BooleanField(default=True)

    def save(self, *a, **kw):
        ''' Ensures that a concept has a correct word count.  Called
        before saving a concept.
        '''
        self.words = len(self.text.split())
        super(Concept, self).save(*a, **kw)
    
    @property
    @cached(lambda self: 'concept_canonical_name_'+self.text, cached.week)
    def canonical_name(self):
        return self.some_surface().text

    def __unicode__(self):
        return u"<" + self.language.id + ": " + self.text + ">"
    
    def get_assertions(self, useful_only=True):
        '''Get all :class:`Assertions` about this concept.'''
        return Assertion.get_filtered(Q(concept1=self) | Q(concept2=self), useful_only=useful_only)

    def get_assertions_forward(self, useful_only=True):
        '''Get all :class:`Assertions` with this concept on the left.'''
        return Assertion.get_filtered(Q(concept1=self), useful_only=useful_only)

    def get_assertions_reverse(self, useful_only=True):
        '''Get all :class:`Assertions` with this concept on the right.'''
        return Assertion.get_filtered(Q(concept2=self), useful_only=useful_only)
    
    def raw_assertions(self):
        got = RawAssertion.objects.filter(
            (Q(assertion__concept1=self) | Q(assertion__concept2=self))
            & Q(score__gt=0) & Q(assertion__score__gt=0)
        )
        return got

    def raw_assertions_no_dupes(self, n=10, related=None):
        from django.db.models import F
        got = RawAssertion.objects.filter(
            (Q(assertion__concept1=self) | Q(assertion__concept2=self))
            & Q(score__gt=0) & Q(assertion__score__gt=0)
            & Q(assertion__best_raw_id=F('id'))
        )
        #all_raw = RawAssertion.objects.filter(
        #    (Q(assertion__concept1=self) | Q(assertion__concept2=self))
        #    & Q(score__gt=0) & Q(assertion__score__gt=0)
        #)
        #if related: all_raw = all_raw.select_related(**related)
        #used = set()
        #got = []
        #for raw in all_raw:
        #    if raw.assertion in used: continue
        #    used.add(raw.assertion)
        #    got.append(raw)
        #    if len(got) >= n: break
        return got
    
    def get_my_right_features(self, useful_only=True):
        '''
        Get all the RightFeatures that have been asserted about this concept.

        Returns a list of (feature, frequency, score, assertion) tuples.
        '''
        return [(RightFeature(a.relation, a.concept2), a.frequency, a.score, a)
                for a in self.get_assertions_forward(useful_only)]

    
    def get_my_left_features(self, useful_only=True):
        '''
        Get all the LeftFeatures that have been asserted about this concept.

        Returns a list of (feature, frequency, score, assertion) tuples.
        '''
        return [(LeftFeature(a.relation, a.concept1), a.frequency, a.score, a)
                for a in self.get_assertions_reverse(useful_only)]

    
    def has_feature(self, feature):
        '''
        Returns True if the concept has the given feature.
        '''
        score = self.score_for_feature(feature)
        return score is not None and score > 0

    def score_for_feature(self, feature):
        try:
            assertions = Assertion.objects.filter(relation=feature.relation)
            if feature.tuple_key == 'left':
                assertions = assertions.filter(concept1=feature.concept,
                                               concept2=self)
            else:
                assertions = assertions.filter(concept1=self,
                                               concept2=feature.concept)
            return max(a.score for a in assertions)
        except ValueError: # what max() throws for an empty sequence
            return None
    
    def group_assertions_by_feature(self, useful_only=True):
        forward_assertions = self.get_assertions_forward(useful_only)\
          .select_related('all_raw__surface2', 'frequency')
        reverse_assertions = self.get_assertions_reverse(useful_only)\
          .select_related('all_raw__surface1', 'frequency')
        thedict = {}
        for a in forward_assertions:
            # FIXME: seems that features no longer have polarity.
            thedict.setdefault(LeftFeature(a.relation, self, a.polarity), [])\
                .append((a.best_raw().surface2.text, a))
        for a in reverse_assertions:
            thedict.setdefault(RightFeature(a.relation, self, a.polarity), [])\
                .append((a.best_raw().surface1.text, a))
        return thedict
    
    def top_assertions_by_feature(self, limit=50, useful_only=True):
        results = []
        manager = Assertion.objects
        # forward relations
        for relation in Relation.objects.all():
            feature = LeftFeature(relation, self)
            filtered = manager.filter(concept1=self, relation=relation,
                                      best_surface2__isnull=False)
            if useful_only:
                filtered = filtered.filter(score__gt=0)
            expanded = filtered.select_related(
                'frequency', 'best_surface2'
            )
            best = expanded[:limit]
            
            described = [(a.best_surface2.text, a.frequency.text,
                          a.frequency.value > 0, a) for a in best]
            if len(described) > 0: results.append((feature, described))
        # backward relations
        for relation in Relation.objects.all():
            feature = RightFeature(relation, self)
            filtered = manager.filter(concept2=self, relation=relation,
                                      best_surface1__isnull=False)
            if useful_only:
                filtered = filtered.filter(score__gt=0)
            expanded = filtered.select_related(
                'frequency', 'best_surface1'
            )
            best = expanded[:limit]
            
            described = [(a.best_surface1.text, a.frequency.text,
                          a.frequency.value > 0, a) for a in best]
            if len(described) > 0: results.append((feature, described))
        results.sort(key=lambda x: -len(x[1]))
        return results

    def some_surface(self):
        """
        Get an arbitrary :class:`SurfaceForm` representing this concept.

        Returns None if the concept has no surface form.
        """
        try:
            return self.surfaceform_set.all()[0]
        except IndexError:
            return None
    
    @classmethod
    def get(cls, text, language, auto_create=False):
        """
        Get the Concept represented by a given string of text.

        If the Concept does not exist, this method will return None by default.
        However, if the parameter ``auto_create=True`` is given, then this will
        create the Concept (adding it to the database) instead.
        
        You should not run the string through a normalizer, or use a string
        which came from :attr:`Concept.text` (which is equivalent). If you
        have a normalized string, you should use :meth:`get_raw` instead.
        """
        if not isinstance(language, Language):
            language = Language.get(language)
        surface = SurfaceForm.get(text, language, auto_create)
        if surface is None:
            return Concept.get_raw(language.nl.normalize(text), language)
        return surface.concept

    @classmethod
    def get_raw(cls, normalized_text, language, auto_create=False):
        """
        Get the Concept whose normalized form is the given string.

        If the Concept does not exist, this method will raise a
        Concept.DoesNotExist exception.  However, if the parameter
        ``auto_create=True`` is given, then this will create the
        Concept (adding it to the database) instead.

        Normalized forms should not be assumed to be stable; they may change
        between releases.
        """
        if auto_create:
            concept_obj, created = cls.objects.get_or_create(text=normalized_text,language=language)
        else:
            concept_obj = cls.objects.get(text=normalized_text,language=language)
        return concept_obj

    @classmethod
    def exists(cls, text, language, is_raw=False):
        '''
        Determine if a concept exists in ConceptNet.

        If `is_raw` is True, `text` is considered to be already in the
        raw (normalized) concept form. Otherwise, it is normalized
        before being checked in the database.
        '''
        if not isinstance(language, Language):
            language = Language.get(language)
        if not is_raw:
            surface = SurfaceForm.get(text, language, False)
            if surface is not None: return True
            text = language.nl.normalize(text)

        return cls.exists_raw(text, language)

    @classmethod
    def exists_raw(cls, normalized_text, language):
        return bool(cls.objects.filter(text=normalized_text, language=language))
            
        
    @classmethod
    @cached(lambda cls, id: 'conceptbyid_%d' % id, cached.minute)
    def get_by_id(cls, id):
        return cls.objects.get(id=id)
    
    def update_num_assertions(self):
        self.num_assertions = self.get_assertions().count()
        self.save()

    # used in commons
    def get_absolute_url(self):
        return '/%s/concept/+%s/' % (self.language.id, urlquote(self.text))
    
    class Meta:
        unique_together = ('language', 'text')
    
        
class UsefulAssertionManager(models.Manager):
    def get_query_set(self):
        return super(UsefulAssertionManager, self).get_query_set().filter(
            score__gt=0, concept1__visible=True, concept2__visible=True
        )


class SurfaceForm(models.Model):
    """
    A SurfaceForm is a string used to express a :class:`Concept` in its natural
    language.
    """
    language = models.ForeignKey(Language)
    concept = models.ForeignKey(Concept)
    text = models.TextField()
    residue = models.TextField()
    use_count = models.IntegerField(default=0)
    
    @staticmethod
    def get(text, lang, auto_create=False):
        if isinstance(lang, basestring):
            lang = Language.get(lang)
        nl = lang.nl
        try:
            known = SurfaceForm.objects.get(language=lang, text=text)
            return known
        except SurfaceForm.DoesNotExist:
            if not auto_create:
                return None
            else:
                lemma, residue = nl.lemma_factor(text)
                concept, created = Concept.objects.get_or_create(language=lang, text=lemma)
                if created: concept.save()

                # use get_or_create so it's atomic
                surface_form, _ = SurfaceForm.objects.get_or_create(concept=concept,
                text=text, residue=residue, language=lang)
                return surface_form
    
    def update_raw(self):
        for raw in self.left_rawassertion_set.all():
            raw.update_assertion()
        for raw in self.right_rawassertion_set.all():
            raw.update_assertion()
    
    def update(self, stem, residue):
        self.concept = Concept.get_raw(stem, self.language, auto_create=True)
        self.residue = residue
        self.save()
        self.update_raw()
        return self
    
    @property
    def urltext(self):
        return urlquote(self.text)
    
    def __unicode__(self):
        return self.text
    
    class Meta:
        unique_together = (('language', 'text'),)
        ordering = ['-use_count']

class Assertion(models.Model, ScoredModel):
    # Managers
    objects = models.Manager()
    useful = UsefulAssertionManager()
    
    language = models.ForeignKey(Language)
    relation = models.ForeignKey(Relation)
    concept1 = models.ForeignKey(Concept, related_name='left_assertion_set')
    concept2 = models.ForeignKey(Concept, related_name='right_assertion_set')
    score = models.IntegerField(default=0)
    frequency = models.ForeignKey(Frequency)
    votes = generic.GenericRelation(Vote)
    
    best_surface1 = models.ForeignKey(SurfaceForm, null=True, related_name='left_assertion_set')
    best_surface2 = models.ForeignKey(SurfaceForm, null=True, related_name='right_assertion_set')
    best_raw_id = models.IntegerField(null=True)
    best_frame = models.ForeignKey(Frame, null=True)
    
    class Meta:
        unique_together = ('relation', 'concept1', 'concept2', 'frequency', 'language')
        ordering = ['-score']
        
    def best_raw(self):
        """
        Get the highest scoring :class:`RawAssertion` for this assertion.
        """
        return self.rawassertion_set.all()[0]
        
    def nl_repr(self, wrap_text=lambda assertion, text: text):
        # FIXME: use the raw cache
        try:
            return self.best_raw().nl_repr(wrap_text)
        except ValueError:
            raise ValueError(str(self))
            return '%s %s %s' % (wrap_text(self, self.concept1.text),
                                 self.relation.name,
                                 wrap_text(self, self.concept2.text))

    def update_raw_cache(self):
        try:
            best_raw = self.best_raw()
        except IndexError: return
        
        self.best_surface1 = best_raw.surface1
        self.best_surface2 = best_raw.surface2
        self.best_frame = best_raw.frame
        self.best_raw_id = best_raw.id
        self.save()
    
    def update_score(self):
        old_score = self.score
        ScoredModel.update_score(self)
        if (self.score == 0) != (old_score == 0):
            self.concept1.update_num_assertions()
            self.concept2.update_num_assertions()
  
    @property
    def creator(self):
        return self.best_raw().creator
        
    @property
    def polarity(self):
        if self.frequency.value >= 0: return 1
        else: return -1

    def __unicode__(self):
        #return "Assertion"
        return u"%s(%s, %s)[%s]" % (self.relation.name, self.concept1.text,
        self.concept2.text, self.frequency.text)
        
    @classmethod
    def get_filtered(cls, *a, **kw):
        useful_only = kw.pop('useful_only', True)
        if useful_only: return cls.useful.filter(*a, **kw)
        else: return cls.objects.filter(*a, **kw)
        
    def get_absolute_url(self):
        return '/%s/assertion/%s/' % (self.language.id, self.id)

# Register signals to make score updates happen automatically.
def denormalize_num_assertions(sender, instance, created=False, **kwargs):
    """
    Keep the num_assertions field up to date.
    """
    instance.concept1.update_num_assertions()
    instance.concept2.update_num_assertions()

## this one isn't actually necessary; redundant with Assertion.update_score
#models.signals.post_save.connect(denormalize_num_assertions, sender=Assertion)
models.signals.post_delete.connect(denormalize_num_assertions, sender=Assertion)

'''
class AssertionVote(models.Model):
    """
    A vote on an Assertion by a User.

    This is temporarily a view of the big Votes table:

    CREATE VIEW temp_assertion_votes AS
      SELECT id, user_id, object_id AS assertion_id, vote
        FROM votes WHERE content_type_id=68;
    """
    user         = models.ForeignKey(User)
    assertion    = models.ForeignKey(Assertion)
    vote         = models.SmallIntegerField(choices=SCORES)

    class Meta:
        db_table = 'temp_assertion_votes'
'''

class RawAssertion(TimestampedModel, ScoredModel):
    """
    A RawAssertion represents the connection between an :class:`Assertion` and
    natural language. Where an Assertion describes a :class:`Relation` between
    two :class:`Concepts`, a RawAssertion describes a sentence :class:`Frame`
    that connects the :class:`SurfaceForms` of those concepts.
    
    A RawAssertion also represents how a particular :class:`Sentence` can
    be interpreted to make an Assertion. :attr:`surface1` and :attr:`surface2`
    generally come from chunks of a sentence that someone entered into Open
    Mind.
    """
    sentence = models.ForeignKey(Sentence, null=True)
    assertion = models.ForeignKey(Assertion, null=True)
    creator = models.ForeignKey(User)
    surface1 = models.ForeignKey(SurfaceForm, related_name='left_rawassertion_set')
    surface2 = models.ForeignKey(SurfaceForm, related_name='right_rawassertion_set')
    frame = models.ForeignKey(Frame)    
    #batch = models.ForeignKey(Batch, null=True)
    language = models.ForeignKey(Language)
    score = models.IntegerField(default=0)
    votes = generic.GenericRelation(Vote)

    class Meta:
        unique_together = ('surface1', 'surface2', 'frame', 'language')
    
    @property
    def relation(self): return self.frame.relation
    @property
    def text1(self): return self.surface1.text
    @property
    def text2(self): return self.surface2.text
    
    def __unicode__(self):
        return u"%(language)s: ('%(text1)s' %(relation)s '%(text2)s') s=%(score)d" % dict(
            language=self.language.id, relation=self.relation.name,
            text1=self.text1, text2=self.text2, score=self.score)

    def nl_repr(self, wrap_text=lambda assertion, text: text):
        """Reconstruct the natural language representation.
        The text concepts are passed to the wrap_text function to
        allow a view to wrap them in a link (or do any other
        transformation.) The prototype for wrap_text is
        :samp:`wrap_text({assertion}, {text})`,
        where *assertion* is this RawAssertion object and *text* is the
        natural-language text of the concept (text1 or text2)."""

        text1 = wrap_text(self, self.surface1.text.strip())
        text2 = wrap_text(self, self.surface2.text.strip())
        return self.frame.fill_in(text1, text2)
        
    def main_sentence(self):
        return self.sentence
        #return self.sentences.all()[0]

    def surface(self, idx):
        """Get either surface1 or surface2, depending on the (1-based) idx."""
        if idx == 1: return self.surface1
        elif idx == 2: return self.surface2
        else: raise KeyError(idx)
    
    def correct_assertion(self, frame, surf1, surf2):
        self.frame = frame
        self.surface1 = surf1
        self.surface2 = surf2
        return self.update_assertion()

    def update_assertion(self):
        """
        Update the connection between this RawAssertion and its Assertion,
        if a Frame or SurfaceForm has changed.
        """
        try:
            matching = Assertion.objects.get(
                concept1=self.surface1.concept,
                concept2=self.surface2.concept,
                relation=self.frame.relation,
                frequency=self.frame.frequency
            )
            if matching is self.assertion:
                # Nothing to be done
                print '  no-op: tried to merge assertion with itself'
                return self.assertion
            # There's an assertion like this already. Merge the two assertions.
            print '  merging assertions'
            print '    '+str(matching)
            for vote in self.assertion.votes.all():
                nvotes = Vote.objects.filter(user=vote.user,
                object_id=matching.id)
                if nvotes == 0:
                    vote.object = matching
                    vote.save()
            self.assertion.update_score()
            self.assertion = matching
            self.assertion.update_score()
            self.save()
            return self.assertion
        except Assertion.DoesNotExist:
            # We can do this just by updating the existing assertion.
            self.assertion.concept1 = self.surface1.concept
            self.assertion.concept2 = self.surface2.concept
            self.assertion.relation = self.frame.relation
            self.assertion.save()
            return self.assertion
    
    @staticmethod
    def make(user, frame, text1, text2, activity, vote=1):
        """
        Create a RawAssertion and a corresponding :class:`Assertion`
        and :class:`Sentence` from user input. Assign votes appropriately.
        
        Requires the following arguments:
        
        - *user*: The user to credit the new assertion to.
        - *frame*: The :class:`Frame` that is being filled in.
        - *text1*: A string filling the first slot of the frame.
        - *text2*: A string filling the second slot of the frame.
        - *activity*: The event that produced this assertion.
        - *vote*: The user's vote on the assertion (often +1, but -1 can occur
          when the user is answering "no" to a question that has not been
          answered before).
        """
        assert text1 != text2
        lang = frame.language
        surface1 = SurfaceForm.get(text1, lang, auto_create=True)
        surface2 = SurfaceForm.get(text2, lang, auto_create=True)
        
        existing = RawAssertion.objects.filter(
            frame=frame,
            surface1=surface1,
            surface2=surface2,
            language=lang
        )
        if len(existing) > 0:
            raw_assertion = existing[0]
        else:
            raw_assertion = RawAssertion.objects.create(
                frame=frame,
                surface1=surface1,
                surface2=surface2,
                language=lang,
                score=0,
                creator=user
            )
        
        assertion, c = Assertion.objects.get_or_create(
            relation=frame.relation,
            concept1=surface1.concept,
            concept2=surface2.concept,
            frequency=frame.frequency,
            language=lang,
            defaults=dict(score=0)
        )
        if c: assertion.save()
        raw_assertion.assertion = assertion
        
        sentence, c = Sentence.objects.get_or_create(
            text=frame.fill_in(text1, text2),
            creator=user,
            language=lang,
            activity=activity,
            defaults=dict(score=0)
        )
        if c:
            lang.sentence_count += 1
            lang.save()
            sentence.save()
        
        Event.record_event(sentence, user, activity)
        sentence.set_rating(user, vote, activity)
        raw_assertion.set_rating(user, vote, activity)
        Event.record_event(raw_assertion, user, activity)
        assertion.set_rating(user, vote, activity)
        Event.record_event(assertion, user, activity)
        
        raw_assertion.sentence = sentence
        raw_assertion.update_score()
        raw_assertion.save()
        return raw_assertion
    
    def update_score(self):
        if self.assertion is not None:
            self.assertion.update_raw_cache()
        ScoredModel.update_score(self)
    
    def get_absolute_url(self):
        return '/%s/statement/%s/' % (self.language.id, self.id)
        
    class Meta:
        ordering = ['-score']
'''
class RawAssertionVote(models.Model):
    """
    A vote on an RawAssertion by a User.

    This is temporarily a view of the big Votes table:

    CREATE VIEW temp_rawassertion_votes AS
      SELECT id, user_id, object_id AS assertion_id, vote
        FROM votes WHERE content_type_id=66;
    """
    user          = models.ForeignKey(User)
    rawassertion = models.ForeignKey(RawAssertion)
    vote          = models.SmallIntegerField(choices=SCORES)

    class Meta:
        db_table = 'temp_rawassertion_votes'
'''
