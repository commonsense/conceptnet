from csc.conceptnet4.models import *

def test_users_do_not_explode():
    a = RawAssertion.objects.filter(language=en)[0]
    a.sentence.creator
    a.sentence.creator.username
