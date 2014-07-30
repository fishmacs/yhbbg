from django.template import Library

from portal import db_util

register = Library()

@register.filter
def get(dt, key):
    return dt.get(key)

@register.filter
def get_category_name(cat):
    return db_util.get_category_name(cat)

@register.filter
def sort_category(cats):
    return sorted(cats)

@register.filter
# True->1 / False->0
# javascript don't accept python's True/False
def to_int(v):
    return int(v)

@register.filter
def mod(x, y):
    return x % y
