from piston.handler import BaseHandler, rc
from piston.doc import generate_doc
from piston.utils import throttle
from piston.authentication import HttpBasicAuthentication
from csc.conceptnet.models import Concept, Relation, SurfaceForm, Frame,\
  Assertion, RawAssertion, LeftFeature, RightFeature, Feature
from csc.corpus.models import Language, Sentence
from csc.nl.models import Frequency
from voting.models import Vote
from events.models import Activity
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from functools import wraps

BASE = "http://openmind.media.mit.edu/api/"
basic_auth = HttpBasicAuthentication()

class LanguageHandler(BaseHandler):
    allowed_methods = ()
    model = Language
    fields = ('id',)

class RelationHandler(BaseHandler):
    allowed_methods = ()
    model = Relation
    fields = ('name',)

def concept_lookup(concept, lang):
    return Concept.get_raw(concept, lang)

def check_authentication(request):
    user = None
    if 'username' in request.POST:
        user = authenticate(username=request.POST['username'],
                            password=request.POST['password'])
    elif 'username' in request.PUT:
        user = authenticate(username=request.PUT['username'],
                            password=request.PUT['password'])
    if user is not None and user.is_active:
        login(request, user)
    else:
        return basic_auth.challenge()

class ConceptHandler(BaseHandler):
    """
    A GET request to this URL will look up a Concept in ConceptNet.
    
    It may not be especially useful to use this query directly, as most of
    the information it gives you back is the information you needed to look it
    up in the first place. However, you can use this to test for a concept's
    existence, and this URL is a base for more interesting queries on concepts.
    """

    allowed_methods = ('GET',)
    model = Concept
    fields = ('text', 'language', 'canonical_name')
    
    @throttle(60, 60, 'read')
    def read(self, request, lang, concept):        
        try:
            return concept_lookup(concept, lang)
        except Concept.DoesNotExist:
            return rc.NOT_FOUND
    
    @staticmethod
    def resource_uri():
        return ('concept_handler', ['language_id', 'text'])
    example_args = {'lang': 'en', 'concept': 'duck'}

class ConceptAssertionHandler(BaseHandler):
    """
    A GET request to this URL will look up all the
    :class:`Assertions <csc.conceptnet.models.Assertion>` that this
    Concept participates in with a score of at least 1.
    
    The results will be limited to the *n* highest-scoring assertions.
    By default, this limit is 20, but you can set it up to 100 by changing
    the *limit* in the URI.
    """
    allowed_methods = ('GET',)

    @throttle(20, 60, 'search')
    def read(self, request, lang, concept, limit=20):
        limit = int(limit)
        if limit > 100: limit = 100
        try:
            return concept_lookup(concept, lang).get_assertions()[:limit]
        except Concept.DoesNotExist:
            return rc.NOT_FOUND

    @staticmethod
    def resource_uri():
        return ('concept_assertion_handler', ['language_id', 'concept', 'limit'])
    example_args = {'lang': 'en', 'concept': 'web%20foot', 'limit': 5}

class ConceptSurfaceHandler(BaseHandler):
    """
    A GET request to this URL will look up all the
    :class:`SurfaceForms <csc.conceptnet.models.SurfaceForm>` that
    correspond to this Concept -- that is, the phrases of natural language
    that are considered to reduce to this Concept.
    
    The results will be limited to *n* surface forms.
    By default, this limit is 20, but you can set it up to 100 by adding
    `limit:n/` to the URI.
    """
    allowed_methods = ('GET',)

    @throttle(20, 60, 'search')
    def read(self, request, lang, concept, limit=20):
        limit = int(limit)
        if limit > 100: limit = 100
        try:
            return concept_lookup(concept, lang).surfaceform_set.all()[:limit]
        except Concept.DoesNotExist:
            return rc.NOT_FOUND

    @staticmethod
    def resource_uri():
        return ('concept_surface_handler', ['language_id', 'concept', 'limit'])
    example_args = {'lang': 'en', 'concept': 'web%20foot', 'limit': 5}

class FeatureHandler(BaseHandler):
    model = Feature
    fields = ('direction', 'relation', 'concept')

    @staticmethod
    def relation_form(lang, dir, relation_name, concept_name):
        return {'direction': dir,
                'relation': {'name': relation_name},
                'resource_uri': "/api/%(lang)s/%(dir)sfeature/%(relation_name)s/%(concept_name)s/" % locals()}

class ConceptFeatureHandler(BaseHandler):
    """
    A GET request to this URL will return a list of all existing
    :class:`Features <csc.conceptnet.models.Features>` built on the given
    :class:`Concept <csc.conceptnet.models.Concept>`.

    The features will be described in a short form: each feature will be a
    dictionary containing its *direction*, the *relation* involved, and the
    *resource_uri* for looking up more information about that feature. The
    concept will be omitted from each feature, because you already know it.
    """

    @throttle(60, 60, 'read')
    def read(self, request, lang, concept):
        try:
            concept = concept_lookup(concept, lang)
        except Concept.DoesNotExist:
            return rc.NOT_FOUND
        left_rels = Assertion.objects.filter(concept1=concept).order_by('relation').values_list('relation__name').distinct()
        right_rels = Assertion.objects.filter(concept2=concept).order_by('relation').values_list('relation__name').distinct()
        
        text = concept.text
        left_repr = [FeatureHandler.relation_form(lang, 'left', rel[0], text) for rel in left_rels]
        right_repr = [FeatureHandler.relation_form(lang, 'right', rel[0], text) for rel in right_rels]
        
        return left_repr + right_repr

    @staticmethod
    def resource_uri():
        return ('concept_feature_handler', ['language_id', 'text'])
    example_args = {'lang': 'en', 'concept': 'moose'}

class FeatureQueryHandler(BaseHandler):
    """
    A GET request to this URL will look up the
    :class:`Assertions <csc.conceptnet.models.Assertion>` that contain a
    certain :class:`Feature <csc.conceptnet.models.Feature>`.
    
    The parameter "{dir}feature" means that the URL should contain either
    `leftfeature/` or `rightfeature/`, depending on what form of feature
    you are looking for. See the :class:`Feature <csc.conceptnet.models.Feature>`
    documentation for more explanation.
    
    As with other queries that return a
    list, this returns 20 results by default, but you may ask for up to 100
    by changing the value of *limit*.
    """
    allowed_methods = ('GET',)

    @throttle(60, 60, 'read')
    def read(self, request, lang, dir, relation, concept, limit=20):
        limit = int(limit)
        if limit > 100: limit=20
        try:
            relation = Relation.objects.get(name=relation)
            concept = concept_lookup(concept, lang)
        except Relation.DoesNotExist:
            return rc.NOT_FOUND
        except Concept.DoesNotExist:
            return rc.NOT_FOUND
        
        if dir == 'left': fclass = LeftFeature
        elif dir == 'right': fclass = RightFeature
        else: return rc.NOT_FOUND
        
        feature = fclass(relation, concept)
        return feature.matching_assertions()[:limit]

    @staticmethod
    def resource_uri():
        return ('feature_query_handler', ['language_id', 'dir', 'relation', 'concept', 'limit'])
    example_args = {'lang': 'en', 'dir': 'right', 'relation': 'HasA',
                    'concept': 'web%20foot', 'limit': 5}

class FrequencyHandler(BaseHandler):
    """
    A GET request to this URL will look up a Frequency modifier by name in
    ConceptNet's natural language module. Each Frequency has a value from
    -10 to 10, so for example, you can use this to determine that
    the English modifier "sometimes" has a value of 4 in ConceptNet.
    """
    
    allowed_methods = ('GET',)
    model = Frequency
    fields = ('text', 'value', 'language')
    
    @throttle(60, 60, 'read')
    def read(self, request, lang, text):
        try:
            return Frequency.objects.get(text=text, language__id=lang)
        except Frequency.DoesNotExist: return rc.NOT_FOUND
    
    @staticmethod
    def resource_uri():
        return ('frequency_handler', ['language_id', 'text'])
    example_args = {'lang': 'en', 'text': 'sometimes'}

class SurfaceFormHandler(BaseHandler):
    """
    A GET request to this URL will look up a SurfaceForm in ConceptNet. The
    SurfaceForm must represent a phrase that someone has used at some point
    on ConceptNet.
    """

    allowed_methods = ('GET',)
    model = SurfaceForm
    fields = ('text', 'concept', 'residue', 'language')
    
    @throttle(60, 60, 'read')
    def read(self, request, lang, text):
        try:
            return SurfaceForm.get(text, lang)
        except SurfaceForm.DoesNotExist: return rc.NOT_FOUND

    @staticmethod
    def resource_uri():
        return ('surface_form_handler', ['language_id', 'text'])
    example_args = {'lang': 'en', 'text': 'have%20webbed%20feet'}

class FrameHandler(BaseHandler):
    """
    A GET request to this URL will look up a sentence frame in a particular
    language, given its ID.
    
    This ID will appear in URLs of other objects,
    such as RawAssertions, that refer to this Frame.
    """
    allowed_methods = ('GET',)
    model = Frame
    fields = ('text', 'relation', 'frequency', 'goodness', 'language')
    
    @throttle(60, 60, 'read')
    def read(self, request, lang, id):
        try:
            return Frame.objects.get(id=id, language__id=lang)
        except Frame.DoesNotExist:
            return rc.NOT_FOUND

    @staticmethod
    def resource_uri():
        return ('frame_handler', ['language_id', 'id'])
    example_args = {'lang': 'en', 'id': '7'}

class AssertionHandler(BaseHandler):
    """
    A GET request to this URL returns information about the Assertion with
    a particular ID.
    
    This ID will appear in URLs of other objects,
    such as RawAssertions, that refer to this Assertion.
    """
    allowed_methods = ('GET',)
    model = Assertion
    fields = ('relation', 'concept1', 'concept2', 'frequency', 'score',
    'language')
    
    @throttle(60, 60, 'read')
    def read(self, request, lang, id):
        try:
            a = Assertion.objects.get(
              id=id, language__id=lang
            )
            return a
        except Assertion.DoesNotExist:
            return rc.NOT_FOUND

    @staticmethod
    def resource_uri():
        return ('assertion_handler', ['language_id', 'id'])
    example_args = {'lang': 'en', 'id': '25'}

class RatedObjectHandler(BaseHandler):
    """
    A GET request to this URL will look up an object that can be voted on
    by users, and show how users have voted on it.
    
    The "type" parameter should either be 'assertion', 'raw_assertion', or
    'sentence', and the "id" should be an object's ID within that type.
    
    This request will return a structure containing the object itself, its
    type, and its list of votes.
    
    A POST request to this URL lets you vote on the object, by supplying
    the parameter `vote` with a value of 1 or -1. You must either have a
    logged-in cookie or send `username` and `password` as additional parameters.
    
    Other optional parameters:
    
    * `activity`: a string identifying what activity or application this
      request is coming from.
    """
    allowed_methods = ('GET', 'POST')
    
    classes = {
        'assertion': Assertion,
        'raw_assertion': RawAssertion,
        'statement': RawAssertion,
        'sentence': Sentence
    }
    
    @throttle(60, 60, 'read')
    def read(self, request, type, lang, id):
        try:
            theclass = RatedObjectHandler.classes[type]
        except KeyError:
            return rc.NOT_FOUND
        try:
            theobj = theclass.objects.get(
                id=id, language__id=lang
            )
            return {'type': type,
                    type: theobj,
                    'votes': theobj.votes.all()}
        except theclass.DoesNotExist:
            return rc.NOT_FOUND

    @throttle(60, 60, 'vote')
    def create(self, request, type, lang, id):
        check_authentication(request)
        try:
            theclass = RatedObjectHandler.classes[type]
        except KeyError:
            return rc.NOT_FOUND
        try:
            theobj = theclass.objects.get(
                id=id, language__id=lang
            )
            user = request.user
            val = int(request.POST['value'])
            activity = Activity.get(request.POST.get('activity', 'Web API'))
            theobj.set_rating(user, val, activity)
            return {'type': type,
                    type: theobj,
                    'votes': theobj.votes.all(),
                    }
        except theclass.DoesNotExist:
            return rc.NOT_FOUND
        except (KeyError, ValueError):
            return rc.BAD_REQUEST

    @staticmethod
    def resource_uri():
        return ('rated_object_handler', ['type', 'language_id', 'id'])
    example_args = {'type': 'assertion', 'lang': 'en', 'id': '25'}

class VoteHandler(BaseHandler):
    allowed_methods = ()
    model = Vote
    fields = ('user', 'vote')

class UserHandler(BaseHandler):
    allowed_methods = ()
    model = User
    fields = ('username',)

class RawAssertionHandler(BaseHandler):
    """
    A GET request to this URL returns information about the RawAssertion
    with a particular ID. This includes the Sentence and Assertion that it
    connects, if they exist.
    """
    allowed_methods = ('GET',)
    model = RawAssertion
    fields = ('frame', 'surface1', 'surface2', 'creator', 'sentence',
              'assertion', 'created', 'updated', 'language', 'score')

    @throttle(60, 60, 'read')
    def read(self, request, lang, id):
        try:
            r = RawAssertion.objects.get(
              id=id, language__id=lang
            )
            return r
        except RawAssertion.DoesNotExist:
            return rc.NOT_FOUND

    @staticmethod
    def resource_uri():
        return ('raw_assertion_handler', ['language_id', 'id'])
    example_args = {'lang': 'en', 'id': '26'}
    
class RawAssertionByFrameHandler(BaseHandler):
    """
    A GET request to this URL lists the RawAssertions that use a particular
    sentence frame, specified by its ID. As with other queries that return a
    list, this returns 20 results by default, but you can ask for up to 100
    by changing the value of *limit*.
    
    A POST request to this URL submits new knowledge to Open Mind. The
    POST parameters `text1` and `text2` specify the text that fills the blanks.
    
    You must either have a logged-in cookie or send `username` and
    `password` as additional parameters.
    
    Other optional parameters:
    * `activity`: a string identifying what activity or application this
      request is coming from.
    * `vote`: either 1 or -1. This will vote for or against the assertion after
      you create it, something you often want to do.
    """
    allowed_methods = ('GET', 'POST')
    @throttle(20, 60, 'search')
    def read(self, request, lang, id, limit=20):
        limit = int(limit)
        if limit > 100: limit = 100
        try:
            return Frame.objects.get(id=id, language__id=lang).rawassertion_set.all()[:limit]
        except Frame.DoesNotExist:
            return rc.NOT_FOUND

    @throttle(5, 60, 'add')
    def create(self, request, lang, id, limit=None):
        check_authentication(request)
        try:
            frame = Frame.objects.get(id=id, language__id=lang)
        except Frame.DoesNotExist:
            return rc.NOT_FOUND
        
        user = request.user
        activity = Activity.get(request.POST.get('activity', 'Web API'))
        text1 = request.POST['text1']
        text2 = request.POST['text2']
        vote = int(request.POST.get('vote', 1))
        raw = RawAssertion.make(user, frame, text1, text2, activity, vote)
        return raw

    @staticmethod
    def resource_uri():
        return ('raw_assertion_by_frame_handler', ['language_id', 'id', 'limit'])

class SentenceHandler(BaseHandler):
    allowed_methods = ()
    model = Sentence
    fields = ('text', 'creator', 'language', 'score', 'created_on')




#Change to be random/concept

class RandomConceptHandler(BaseHandler):
    """
    A GET request to this URL returns the id of a random Concept

    """
    allowed_methods = ('GET',)
    #model = RawAssertion.objects.filter(score__gt=2, language=lang
    #fields = ('frame', 'surface1', 'surface2', 'creator', 'sentence',
    #          'assertion', 'created', 'updated', 'language', 'score')

    @throttle(60, 60, 'read')
    def read(self, request, lang, score_thresh=2, num=2):
        print "I'm in random"
        assertions = RawAssertion.objects.filter(score__gt=score_thresh, language=lang).select_related('surface1').order_by('?')

        random_concepts = {}

        i = 0
        while len(random_concepts) < num and i < len(assertions):
            #Gets the first concept from the assertion
            concept = assertions[i].surface1

            #Adds it to the set, to make sure we're not adding duplicates
            random_concepts.add(concept)
            i += 1

        random_concepts_dict = {}
        for c in random_concepts:
            random

        return random_concepts
                #{'type': type,
                #    type: theobj,
                #    'votes': theobj.votes.all()}

    @staticmethod
    def resource_uri():
        return ('random_concept_handler', ['language_id', 'score_thresh', 'number'])
    #example_args = {'lang': 'en', 'id': '26'}

