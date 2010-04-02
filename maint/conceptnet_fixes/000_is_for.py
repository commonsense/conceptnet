from csc.conceptnet.models import *
from csc.util import foreach

target_frame = Frame.objects.get(language=en, relation__name='UsedFor', text='{1} is for {2}')

def queryset1():
    frame = Frame.objects.get(text='{1} is {2}', language=en, relation__name='HasProperty')
    got = RawAssertion.objects.filter(language=en, frame=frame)
    return got

def queryset2():
    frame = Frame.objects.get(text='{1} is {2}', language=en, relation__name='ReceivesAction')
    got = RawAssertion.objects.filter(language=en, frame=frame)
    return got

def fix_is_for(s):
    if s.surface2.text.startswith('for '):
        print s
        newsurf = SurfaceForm.get(s.surface2.text[4:], 'en', auto_create=True)
        print "=>",
        print s.correct_assertion(target_frame, s.surface1, newsurf)

foreach(queryset1(), fix_is_for)

