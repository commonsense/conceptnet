"""
`rest_client.py`_ is a simple client for interacting with ConceptNet 4's REST
API.

.. _`rest_client.py`: http://openmind.media.mit.edu/media/rest_client.py

This client is not object-oriented. The data structures you work with are
dictionaries, of the form described in the API documentation. The main function
:func:`lookup` can be used to look up many different kinds of data. There are
also convenience functions for performing common operations on this data.

If you want to know what fields are contained in these dictionaries, read
the REST API documentation at
http://csc.media.mit.edu/docs/conceptnet/webapi.html#rest-requests .
"""

import urllib, urllib2

try:
    import json
except:
    import simplejson as json

SERVER_URL = 'http://openmind.media.mit.edu'
API_URL = 'http://openmind.media.mit.edu/api/'
CLIENT_VERSION = '1'

def lookup(type, language, key):
    """
    Get an object of a certain *type*, specified by the code for what
    *language* it is in and its *key*. The types currently supported are:

        `assertion`
            Use the `id` as the key.
        `concept`
            Use the concept's raw name as the key.
        `frame`
            Use the `id` as the key.
        `frequency`
            Use the adverb text as the key. For the default frequency, this
            will be the null string.
        `raw_assertion`
            Use the `id` as the key.
        `surface`
            A SurfaceForm. Use the text as the key.
        `leftfeature`
            This will return a list of assertions with a specified left
            feature. The key takes the form `relation/concept`. For example,
            the key `PartOf/wheel` looks up all assertions saying a wheel is
            part of something.
        `rightfeature`
            This, similarly, returns a list of assertions with a specified
            right feature. The key takes the form `relation/concept`. For
            example, the key `PartOf/car` looks up all assertions that say
            something is part of a car.
    
    The object will be returned as a dictionary, or in the case of features,
    a list.
    """
    return _get_json(language, type, key)

def lookup_concept_raw(language, concept_name):
    """
    Look up a Concept by its language and its raw name. For example,
    `lookup_concept_raw('en', 'webbed feet')` will get no results, but
    `lookup_concept_raw('en', 'web foot')` will.

    Use :func:`lookup_concept_from_surface` to look up a concept from an
    existing surface text, such as "webbed feet".

    Use :func:`lookup_concept_from_nl` to look up a concept from any natural
    language text. This requires the `csc.nl` module.
    """
    return lookup('concept', language, concept_name)

def lookup_concept_from_surface(language, surface_text):
    """
    Look up a concept, given a surface form of that concept that someone has
    entered into Open Mind. For example,
    `lookup_concept_from_surface('en', 'webbed feet')` will return the concept
    'web foot'.
    """
    surface = lookup('surface', language, surface_text)
    return surface['concept']

def lookup_concept_from_nl(language, text):
    """
    Look up a concept using any natural language text that represents it.
    This function requires the :mod:`csc.nl` module, or the `standalone_nlp`
    version of it, to normalize natural language text into a raw concept name
    """
    try:
        from csc import nl
    except ImportError:
        import standalone_nlp as nl

    nltools = nl.get_nl(language)
    normalized = nltools.normalize(text)
    return lookup_concept_raw(language, normalized)

def assertions_for_concept(concept, direction='all', limit=20):
    """
    Given a dictionary representing a concept, look up the assertions it
    appears in.

    By default, this returns all matching assertions. By setting the
    optional argument `direction` to "forward" or "backward", you can restrict
    it to only assertions that have that concept on the left or the right
    respectively.

    You may set the limit on the number of results up to 100. The default is
    20. This limit is applied before results are filtered for forward or
    backward assertions.
    """
    def assertion_filter(assertion):
        if direction == 'all': return True
        elif direction == 'forward':
            return assertion['concept1']['text'] == concept['text']
        elif direction == 'backward':
            return assertion['concept2']['text'] == concept['text']
        else:
            raise ValueError("Direction must be 'all', 'forward', or 'backward'")
        
    assertions = _refine_json(concept, 'assertions', 'limit:%d' % limit)
    return [a for a in assertions if assertion_filter(a)]

def surface_forms_for_concept(concept, limit=20):
    """
    Given a dictionary representing a concept, get a list of its surface
    forms (also represented as dictionaries).

    You may set the limit on the number of results up to 100. The default is
    20.
    """
    return _refine_json(concept, 'surfaceforms', 'limit:%d' % limit)

def votes_for(obj):
    """
    Given a dictionary representing any object that can be voted on -- such as
    an assertion or raw_assertion -- get a list of its votes.
    """
    return _refine_json(obj, 'votes')

def add_statement(language, frame_id, text1, text2, username, password):
    """
    Add a statement to Open Mind, or vote for it if it is there.

    Requires the following parameters:
        
        language
            The language code, such as 'en'.
        frame_id
            The numeric ID of the sentence frame to use.
        text1
            The text filling the first blank of the frame.
        text2
            The text filling the second blank of the frame.
        username
            Your Open Mind username.
        password
            Your Open Mind password.
    
    Example: 
    >>> frame = lookup('frame', 'en', 7)
    >>> frame['text']
    '{1} is for {2}'
    
    >>> add_statement('en', 7, 'election day', 'voting', 'rspeer', PASSWORD)
    (Result: rspeer adds the statement "election day is for voting", which
    is also returned as a raw_assertion.)
    """
    return _post_json([language, 'frame', frame_id, 'statements'], {
        'username': username,
        'password': password,
        'text1': text1,
        'text2': text2
    })

def _get_json(*url_parts):
    url = API_URL + '/'.join(urllib2.quote(str(p)) for p in url_parts) + '/query.json'
    return json.loads(_get_url(url))

def _post_json(url_parts, post_parts):
    url = API_URL + '/'.join(urllib2.quote(str(p)) for p in url_parts) + '/query.json'
    postdata = urllib.urlencode(post_parts)
    req = urllib2.Request(url, postdata)
    response = urllib2.urlopen(req)
    return json.loads(response.read())

def _extend_url(old_url, *url_parts):
    url = old_url + '/'.join(urllib2.quote(str(p)) for p in url_parts) + '/'
    return json.loads(_get_url(url))

def _get_url(url):
    conn = urllib2.urlopen(url)
    return conn.read()

def _refine_json(old_obj, *parts):
    return _extend_url(SERVER_URL + old_obj['resource_uri'], *parts)

