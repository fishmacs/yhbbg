#encoding=utf8

from django.template import Library

from bookbag.common import global_def as common_def
from cms import decorator

register = Library()

# @register.filter
# def show_user_type(user_type):
#     return common_def.USER_TYPES[user_type][0]


@register.filter
def grade_name(grade):
    return common_def.get_grade_display(grade)


@register.filter
def user_has_perms(user, permstr):
    return decorator.check_all_perms(user, permstr)


@register.filter
def user_has_perm(user, permstr):
    return decorator.check_any_perm(user, permstr)


@register.filter
def range(n, start=0):
    return xrange(start, start+n)


@register.filter
def split(s, delimiter=' '):
    return s.split(delimiter)
