## python 2.6 does not have OrderedDict
try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict
    
from django.views.decorators.cache import cache_page

from models import Test
from portal.decorator import authenticated_required
from common.decorator import json_wrapper


@authenticated_required
@cache_page(300)
@json_wrapper
def get_test(request, courseware_id):
    qs = Test.objects.filter(courseware=courseware_id)
    sections = OrderedDict()
    for t in qs:
        section = sections.setdefault(t.section, [])
        t1 = {'id': t.id,
              'title': str(len(section) + 1),
              'type': t.get_type(),
              'num': t.num,
              'answer': t.get_answer(),
              'page': t.page,
              'grid': t.grid,
              'hint': t.hint}
        section.append(t1)
    return [{'title': k, 'questions': v} for k, v in sections.iteritems()]
