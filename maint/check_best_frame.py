from csc.util import queryset_foreach
from csc.conceptnet4.models import Frame, Assertion, RawAssertion, SurfaceForm
from django.db import connection

def check_frame(assertion):
    try:
        assertion.best_frame
    except Frame.DoesNotExist:
        print "No frame for:", assertion
        assertion.best_frame = None
        assertion.save()
    
    try:
        assertion.best_raw
        assertion.best_surface1
        assertion.best_surface2
    except (RawAssertion.DoesNotExist, SurfaceForm.DoesNotExist):
        print "No raw assertion for:", assertion
        assertion.best_raw = None
        assertion.best_surface1 = None
        assertion.best_surface2 = None
        assertion.save()

queryset_foreach(Assertion.objects.all(), check_frame,
  batch_size=100)

