from django.conf.urls.defaults import *
from piston.resource import Resource
from csc.webapi.docs import documentation_view
from csc.webapi.handlers import *

# This gives a way to accept "query.foo" on the end of the URL to set the
# format to 'foo'. "?format=foo" works as well.
Q = r'(query\.(?P<emitter_format>.+))?$'

urlpatterns = patterns('',
    url(r'^(?P<lang>[^/]+)/'+Q,
        Resource(LanguageHandler), name='language_handler'),
    url(r'^(?P<lang>.+)/concept/(?P<concept>[^/]*)/'+Q,
        Resource(ConceptHandler), name='concept_handler'),
    url(r'^(?P<lang>.+)/concept/(?P<concept>[^/]*)/assertions/'+Q,
        Resource(ConceptAssertionHandler), name='concept_assertion_handler_default'),
    url(r'^(?P<lang>.+)/concept/(?P<concept>[^/]*)/assertions/limit:(?P<limit>[0-9]+)/'+Q,
        Resource(ConceptAssertionHandler), name='concept_assertion_handler'),
    url(r'^(?P<lang>.+)/concept/(?P<concept>[^/]*)/surfaceforms/'+Q,
        Resource(ConceptSurfaceHandler), name='concept_surface_handler_default'),
    url(r'^(?P<lang>.+)/concept/(?P<concept>[^/]*)/surfaceforms/limit:(?P<limit>[0-9]+)/'+Q,
        Resource(ConceptSurfaceHandler), name='concept_surface_handler'),
    url(r'^(?P<lang>.+)/concept/(?P<concept>[^/]*)/features/'+Q,
        Resource(ConceptFeatureHandler), name='concept_feature_handler'),
    url(r'^(?P<lang>.+)/(?P<dir>left|right)feature/(?P<relation>[^/]+)/(?P<concept>[^/]+)/'+Q,
        Resource(FeatureQueryHandler), name='feature_query_handler_default'),
    url(r'^(?P<lang>.+)/(?P<dir>left|right)feature/(?P<relation>[^/]+)/(?P<concept>[^/]+)/limit:(?P<limit>[0-9]+)/'+Q,
        Resource(FeatureQueryHandler), name='feature_query_handler'),
    url(r'^(?P<lang>.+)/(?P<type>.+)/(?P<id>[0-9]+)/votes/'+Q,
        Resource(RatedObjectHandler), name='rated_object_handler'),
    url(r'^(?P<lang>.+)/surface/(?P<text>.+)/'+Q,
        Resource(SurfaceFormHandler), name='surface_form_handler'),
    url(r'^(?P<lang>.+)/frame/(?P<id>[0-9]+)/'+Q,
        Resource(FrameHandler), name='frame_handler'),
    url(r'^(?P<lang>.+)/frame/(?P<id>[0-9]+)/statements/'+Q,
        Resource(RawAssertionByFrameHandler),
        name='raw_assertion_by_frame_handler_default'),
    url(r'^(?P<lang>.+)/frame/(?P<id>[0-9]+)/statements/limit:(?P<limit>[0-9]+)/'+Q,
        Resource(RawAssertionByFrameHandler),
        name='raw_assertion_by_frame_handler'),
    url(r'^(?P<lang>.+)/assertion/(?P<id>[0-9]+)/'+Q,
        Resource(AssertionHandler), name='assertion_handler'),
    url(r'^(?P<lang>.+)/assertion/(?P<id>[0-9]+)/raw/'+Q,
        Resource(AssertionToRawHandler), name='assertion_to_raw_handler'),
    url(r'^(?P<lang>.+)/raw_assertion/(?P<id>[0-9]+)/'+Q,
        Resource(RawAssertionHandler), name='raw_assertion_handler'),
    url(r'^(?P<lang>.+)/frequency/(?P<text>[^/]*)/'+Q,
        Resource(FrequencyHandler), name='frequency_handler'),
    url(r'^(?P<lang>.+)/assertionfind/(?P<relation>[^/]+)/(?P<text1>[^/]+)/(?P<text2>[^/]+)/'+Q,
        Resource(AssertionFindHandler), name='assertion_find_handler'),
    url(r'^user/(?P<username>.+)/'+Q,
        Resource(UserHandler), name='user_handler'),
    url(r'docs.txt$',
        documentation_view, name='documentation_view')
)
# :vim:tw=0:nowrap:
