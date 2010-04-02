from django.conf.urls.defaults import *
from csamoa.representation.presentation.models import Predicate

urlpatterns = patterns('csamoa.realm.views',
    url(r'^concept/', 'get_stemid'),
    url(r'^concept/(?P<id>\d+)/all', 'get_stem_allforms'),
)

# URLs:
# GET /concept/?text={text,...}&language={language}
#  -> gets concept id(s) for text(s)
# GET /concept/{id}/canonical/ -> gets canonical form for concept
# GET /concept/{id}/all/ -> gets all forms for concept
# GET /concept/{id,...}/context -> gets context for the concept(s)


# # Programmatically define the API
# api = {
#     'concept': {
#         '__required': {
#             'language': TextField,
#             },
#         'id': Function(get_stemid,
