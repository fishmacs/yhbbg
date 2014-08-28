import json
import itertools

## python 2.6 does not have OrderedDict
try:
    from collections import OrderedDict
except:
    from ordereddict import OrderedDict

from django.contrib.auth.models import User
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt

from models import Test, TestResult
from portal.decorator import authenticated_required
from common.decorator import json_wrapper


@authenticated_required
@cache_page(300)
@json_wrapper
def get_test(request, courseware_id):
    qs = Test.objects.filter(courseware=courseware_id)
    sections = OrderedDict()
    for t in qs[:20]:
        section = sections.setdefault(t.section, [])
        t1 = {'id': t.id,
              'title': t.title,  # str(len(section) + 1),
              'type': t.get_type(),
              'num': t.num,
              'answer': t.get_answer(),
              'page': t.page,
              'grid': t.grid,
              'hint': t.hint}
        section.append(t1)
    return [{'title': k, 'questions': v} for k, v in sections.iteritems()]
    

@authenticated_required
@csrf_exempt
@json_wrapper
def put_result(request):
    data = json.loads(request.REQUEST['result'])
    t = Test.objects.get(id=data['id'])
    answer = data['answer']
    score = _check_answer(answer, t)
    answer = json.dumps(answer, ensure_ascii=False)
    try:
        r = TestResult.objects.get(user=request.user, test=t)
        r.answer = answer
        r.score = score
        r.save()
    except TestResult.DoesNotExist:
        TestResult.objects.create(
            user=request.user, test_id=t.id,
            answer=answer, score=score
        )
        

@authenticated_required
@json_wrapper
def result_list(request, courseware_id, class_id):
    tests = Test.objects.filter(courseware=courseware_id)
    results = TestResult.objects.select_related('test', 'user').filter(test__in=tests)
    if class_id == 'personal':
        users = [request.user]
        results = results.filter(user=request.user)
    else:
        users = User.objects.filter(userprofile__myclass_id=class_id)
        results = results.filter(user__in=users).order_by('user__username')
    resultdict = dict([((r.test_id, r.user_id), r) for r in results])
    data = OrderedDict()
    for u in users:
        result = data.setdefault(u.username, {})
        for t in tests:
            section = result.setdefault(t.section, [])
            try:
                r = resultdict[(t.id, u.id)]
                section.append({'title': t.title, 'score': r.score, 'answer': r.get_answer()})
            except KeyError:
                section.append({'title': t.title, 'score': -1, 'answer': []})
    result = []
    for username, sections in data.iteritems():
        new_sections = []
        for name, questions in sections.iteritems():
            new_sections.append({'title': name, 'questions': questions})
        result.append({'username': username, 'result': new_sections})
    return result


def _check_answer(myanswer, test):
    if test.has_answer:
        if test.is_fill:
            standards = [s.split(';') for s in test.get_answer()]
            standards = itertools.product(*standards)
            for x in standards:
                if myanswer == list(x):
                    return 1
            return 0
        else:
            return 1 if sorted(myanswer) == sorted(test.get_answer()) else 0
    return -2
    