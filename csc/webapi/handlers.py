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
    """
    A GET request to this URL will show basic information about a language --
    its ID and how many sentences (parsed or unparsed) exist in the database
    for that language.

    The sentence count is a cached value. It might become out of sync with the
    actual number of sentences, but it's not supposed to.
    """
    allowed_methods = ('GET',)
    model = Language
    fields = ('id',)
    
    @throttle(600, 60, 'read')
    def read(self, request, lang):
        try:
            lang = Language.get(lang)
            return {'id': lang.id, 'sentence_count': lang.sentence_count}
        except Language.DoesNotExist:
            return rc.NOT_FOUND

    # This is how you make examples for things that don't announce their own
    # resource_uri.
    example_uri = '/api/ja/'
    example_uri_template = '/api/{lang}/'

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
    
    @throttle(600, 60, 'read')
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
    the *limit* in the URL.
    """
    allowed_methods = ('GET',)

    @throttle(200, 60, 'search')
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

    @throttle(200, 60, 'search')
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

    @throttle(600, 60, 'read')
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

    @throttle(600, 60, 'read')
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
    
    @throttle(600, 60, 'read')
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
    
    @throttle(600, 60, 'read')
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
    
    @throttle(600, 60, 'read')
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

class AssertionToRawHandler(BaseHandler):
    """
    A GET request to this URL will list the RawAssertions (natural language
    statements) associated with a given Assertion ID.
    """
    @throttle(200, 60, 'search')
    def read(self, request, lang, id):
        raw_list = RawAssertion.objects.filter(language__id=lang, assertion__id=id)
        return raw_list

    @staticmethod
    def resource_uri():
        return ('assertion_to_raw_handler', ['language_id', 'assertion_id'])
    example_args = {'lang': 'en',
                    'id': 31445}

class AssertionFindHandler(BaseHandler):
    """
    A GET request to this URL will return an Assertion
    given the text of its two concepts and its relation.

    - `relation` is the name of the relation.
    - `text1` is the text of the first concept.
    - `text2` is the text of the second concept.
    
    The concept text can actually be any surface form that normalizes to that
    concept.

    If such an assertion exists, it will be returned. If not, you will get a
    404 response. You can use this to find out whether the assertion exists or
    not.
    """

    allowed_methods = ('GET',)

    @throttle(200, 60, 'search')
    def read(self, request, lang, relation, text1, text2):
        try:
            concept1 = concept_lookup(text1, lang)
            concept2 = concept_lookup(text2, lang)
            relation = Relation.objects.get(name=relation)
        except Concept.DoesNotExist:
            return rc.NOT_FOUND
        except Relation.DoesNotExist:
            return rc.NOT_FOUND

        assertion = Assertion.objects.filter(concept1=concept1, concept2=concept2, relation=relation).order_by('relation').distinct()

        return assertion


        
    @staticmethod
    def resource_uri():
        return ('assertion_find_handler', ['language_id', 'relation', 'text1', 'text2'])
    example_args = {'lang': 'en', 'relation': 'IsA', 'text1': 'dog', 'text2': 'animal'}

        
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
    
    @throttle(600, 60, 'read')
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

    @throttle(600, 60, 'vote')
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
    """
    **Checking users**: A GET request to this URL will confirm whether a user
    exists. If the user exists, this returns a data structure containing their
    username. If the user does not exist, it returns a 404 response.

    **Creating users**: A POST request to this URL will create a user that does
    not already exist. This takes two additional POST parameters:

    - `password`: The password the new user should have.
    - `email`: (Optional and not very important) The e-mail address to be
      associated with the user in the database.

    Do not use high-security passwords here. You're sending them over plain
    HTTP, so they are not encrypted.
    """
    allowed_methods = ('GET', 'POST')
    model = User
    fields = ('username',)

    @throttle(600, 60, 'read')
    def read(self, request, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return rc.NOT_FOUND

    @throttle(200, 60, 'add')
    def create(self, request, username):
        password = request.POST['password']
        email = request.POST.get('email', '')
        exists = User.objects.filter(username=username).count()
        if exists > 0:
            return rc.DUPLICATE_ENTRY
        else:
            return User.objects.create_user(username, email, password)

    example_uri = '/api/user/verbosity/'
    example_uri_template = '/api/user/{username}/'

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

    @throttle(600, 60, 'read')
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
    **Getting assertions**: A GET request to this URL lists the RawAssertions
    that use a particular
    sentence frame, specified by its ID. As with other queries that return a
    list, this returns 20 results by default, but you can ask for up to 100
    by changing the value of *limit*.
    
    **Adding assertions**: A POST request to this URL submits new knowledge to
    Open Mind. The
    POST parameters `text1` and `text2` specify the text that fills the blanks.
    
    You must either have a logged-in cookie or send `username` and
    `password` as additional parameters.
    
    Other optional parameters:

    - `activity`: a string identifying what activity or application this
      request is coming from.
    - `vote`: either 1 or -1. This will vote for or against the assertion after
      you create it, something you often want to do.
    """
    allowed_methods = ('GET', 'POST')
    @throttle(200, 60, 'search')
    def read(self, request, lang, id, limit=20):
        limit = int(limit)
        if limit > 100: limit = 100
        try:
            return Frame.objects.get(id=id, language__id=lang).rawassertion_set.all()[:limit]
        except Frame.DoesNotExist:
            return rc.NOT_FOUND

    @throttle(200, 60, 'add')
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



