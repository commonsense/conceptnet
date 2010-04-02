from csc.conceptnet.models import *
from csc.util import foreach

target_frame = Frame.objects.get(language=en, relation__name='UsedFor', text='{1} is for {2}')

def queryset():
    frame = Frame.objects.get(text='{1} are {2}', language=en, relation__name='IsA')
    got = RawAssertion.objects.filter(language=en, frame=frame)
    return got

def fix(s):
    if s.surface2.text.startswith('for '):
        print s
        newsurf = SurfaceForm.get(s.surface2.text[4:], 'en', auto_create=True)
        print "=>",
        print s.correct_assertion(target_frame, s.surface1, newsurf)

foreach(queryset(), fix)

