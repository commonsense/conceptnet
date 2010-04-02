from csc.conceptnet.models import *
from csc.util import foreach

def fix_spaces(s):
    if (s.surface1.text.startswith(' ') or s.surface2.text.startswith(' ')):
        print s
        newsurf1 = SurfaceForm.get(s.surface1.text.strip(), s.language,
          auto_create=True)
        newsurf2 = SurfaceForm.get(s.surface2.text.strip(), s.language,
          auto_create=True)
        print "=>",
        print s.correct_assertion(s.frame, newsurf1, newsurf2)
        s.save()

foreach(RawAssertion.objects.filter(language__id='zh-Hant'), fix_spaces)

