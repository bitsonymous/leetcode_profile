# myapp/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='range')
def range_filter(value, arg):
    return range(value, arg)
