#encoding=utf8

from django.template import Library

from common import global_def as common_def

register = Library()

@register.filter
def grade_name(grade):
    return common_def.get_grade_display(grade)
