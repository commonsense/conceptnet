from django.template.defaultfilters import stringfilter
from django import template

register = template.Library()

@stringfilter
def indent(value, spaces):
    indentation = ' '*int(spaces)
    return '\n'.join(indentation+line for line in value.split('\n')).strip()
register.filter('indent', indent)