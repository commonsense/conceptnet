from django.contrib import admin
from csc.conceptnet4.models import Frequency, Frame, RawAssertion, Concept,\
Assertion, Relation

for model in (RawAssertion, Concept, Assertion, Relation):
    admin.site.register(model)

class FrequencyAdmin(admin.ModelAdmin):
    list_display = ('language', 'text', 'value')
    list_filter = ('language',)
admin.site.register(Frequency, FrequencyAdmin)

class FrameAdmin(admin.ModelAdmin):
    list_display = ('id', 'language','relation','text','preferred')
    list_filter = ('language','relation')
    list_per_page = 100
    fields = ('relation', 'text', 'language', 'goodness', 'frequency')
admin.site.register(Frame, FrameAdmin)
