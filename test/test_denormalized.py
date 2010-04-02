from nose.tools import *
from csc.conceptnet.models import *
from nose.plugins.attrib import *

activity = Activity.objects.get_or_create(name="nosetests")[0]
user1 = User.objects.get(username='rspeer')
user2 = User.objects.get(username='kcarnold')

def test_denormalized():
    testconcept = Concept.get('test', 'en')

    raw = RawAssertion.make(
      user=user1,
      frame=Frame.objects.get(language=en, relation__name='HasProperty',
                              text='{1} is {2}'),
      text1='the test',
      text2='successful',
      activity=activity)
    raw.set_rating(user2, 0, activity)
    raw.set_rating(user1, 0, activity)
    raw.delete()
    raw.assertion.delete()

    testconcept.update_num_assertions()
    num = testconcept.num_assertions

    raw = RawAssertion.make(
      user=user1,
      frame=Frame.objects.get(language=en, relation__name='HasProperty',
                              text='{1} is {2}'),
      text1='the test',
      text2='successful',
      activity=activity)
    raw_id = raw.id 

    raw = RawAssertion.objects.get(id=raw_id)
    assert raw.score == 1
    
    testconcept = Concept.get('test', 'en')
    assert testconcept.num_assertions == (num + 1)

    raw.set_rating(user2, 1, activity)

    raw = RawAssertion.objects.get(id=raw_id)
    assert raw.score == 2
    
    testconcept = Concept.get('test', 'en')
    assert testconcept.num_assertions == (num + 1)

    raw.set_rating(user2, 0, activity)
    raw.set_rating(user1, 0, activity)
    raw.assertion.set_rating(user2, 0, activity)
    raw.assertion.set_rating(user1, 0, activity)

    testconcept = Concept.get('test', 'en')
    assert testconcept.num_assertions == num
    
    raw = RawAssertion.objects.get(id=raw_id)
    assert raw.score == 0

if __name__ == '__main__':
    test_denormalized()
