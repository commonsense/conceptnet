from django.conf.urls.defaults import *
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
     # Web API (REST)
     (r'', include('csc.webapi.urls')),
     (r'^api/', include('csc.webapi.urls')),

#     # ConceptTools (realm)
#     (r'^api/', include('realm.urls')),
)
