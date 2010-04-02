from django.contrib import admin
from csc.nl.models import (
    AutoreplaceRule, FunctionWord, FunctionClass)

admin.site.register(AutoreplaceRule)
admin.site.register(FunctionClass)

class FunctionWordAdmin(admin.ModelAdmin):
    ordering = ('language', 'word')
admin.site.register(FunctionWord, FunctionWordAdmin)

