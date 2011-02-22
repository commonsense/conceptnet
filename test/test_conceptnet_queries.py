from nose.tools import *
from conceptnet.models import *
from nose.plugins.attrib import *
def setup():
    en = Language.get('en')

def test_assertions_exist():
    Assertion.objects.filter(language=en)[0]
    Assertion.objects.filter(language=Language.get('pt'))[0]
    Assertion.objects.filter(language=Language.get('ja'))[0]
    Assertion.objects.filter(language=Language.get('ko'))[0]
    Assertion.objects.filter(language=Language.get('zh-Hant'))[0]

def test_relations():
    relations = [a.relation.name for a in Assertion.objects.filter(concept1__text='dog', concept2__text='bark', language=en)]
    assert u'CapableOf' in relations

def test_get():
    Concept.get('dog', 'en')
    Concept.get('the dog', 'en')
    Concept.get('dogs', 'en')
    Concept.get_raw('dog', 'en')

@raises(Concept.DoesNotExist)
def test_normalize():
    Concept.get_raw('the dog', 'en')

def test_surface_forms():
    surfaces = [s.text for s in SurfaceForm.objects.filter(concept__text='run', language=en)]
    assert u'run' in surfaces
    assert u'to run' in surfaces
    assert u'running' in surfaces

@attr('postgres')
def test_raw_assertion_search():
    raw = RawAssertion.objects.filter(surface1__concept__text='couch',
          surface2__concept__text='sit', language=en)
    assert len(raw) > 0

