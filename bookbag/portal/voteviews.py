import json
from datetime import datetime

from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

import util
import db_util
import voteq
from decorator import authenticated_required
from common.mongo_models import Vote, UserLog, EmbeddedUser


@authenticated_required
def get_course_controller(request):
    courses = db_util.get_course_list1(request.user, request.session)
    #print 'course list', courses
    course_ids = ['%d_%d' % (cid, course.id) for cid, course in courses]
    # vote_courses = Vote.objects.filter(
    #     started=True, finished=False, deleted=False,
    #     owner__id__in=course_ids).distinct('owner')
    # ret = []
    # for course in vote_courses:
    #     course_id = course['id']
    #     ret.append({'course_id': course_id,
    #                 'destination': '/topic/%s__%s'
    #                 % (course['kind'], course_id),
    #                 'message_queue': settings.MESSAGE_QUEUE})
    ret = [{'course_id': id, 'destination': '/topic/course__' + id,
            'message_queue': settings.MESSAGE_QUEUE}
           for id in course_ids]
    return HttpResponse(json.dumps(ret))


def _extract_vote(vote, user_id):
    choices = []
    for answer in vote.result:
        if answer.voter.id == user_id:
            choices = answer.choices
            break
    # if vote.kind != 'single' and choices:
    #     options = _sort_options(choices, vote.options)
    # else:
    options = [_dict_of_option(o) for o in vote.options]
    for i in choices:
        options[i]['selected'] = True
    return {
        'destination': '/dsub/vote' + str(vote.id),
        'vote_id': str(vote.id),
        'title': vote.title,
        'start_time': vote.start_time.strftime('%Y-%m-%d %H:%M:%S')
        if vote.start_time else '',
        'type': vote.kind,
        'end_time': vote.end_time.strftime('%Y-%m-%d %H:%M:%S')
        if vote.end_time else '',
        'started': vote.started,
        'finished': vote.finished,
        'max_choice': vote.max_choice,
        'min_choice': vote.min_choice,
        'voter_count': vote.voter_count,
        'options': options,
        'voted': len(choices) > 0,
        'message_queue': settings.MESSAGE_QUEUE,
    }


@authenticated_required
def vote_list(request, course_id):
    votes = Vote.objects.filter(owner__id=course_id,
                                deleted=False).exclude(
        'owner', 'creator', 'modifier').order_by(
        'started', 'finished', '-start_time')
    ret = [_extract_vote(v, str(request.user.id)) for v in votes]
    return HttpResponse(json.dumps(ret, ensure_ascii=False))


@authenticated_required
def vote_start(request, vote_id):
    vote = Vote.objects.get(pk=vote_id)
    vote.started = True
    vote.start_time = datetime.now()
    vote.save()
    voteq.send({'command': 'start_vote',
                'vote_id': str(vote.id),
                'title': vote.title,
                'owner': '%s__%s' % (vote.owner.kind, vote.owner.id),
                'type': vote.kind,
                #'voter_count': vote.voter_count,
                'options': [{'content': o.content} for o in vote.options]})
    return HttpResponse(json.dumps({'result': 'ok'}))


@authenticated_required
def vote_end(request, vote_id):
    vote = Vote.objects.get(pk=vote_id)
    vote.finished = True
    vote.end_time = datetime.now()
    vote.save()
    voteq.send({'command': 'end_vote',
                'vote_id': str(vote.id),
                'owner': '%s__%s' % (vote.owner.kind, vote.owner.id)})
    return HttpResponse(json.dumps({'result': 'ok'}))


def _dict_of_option(o, selected=False):
    return {'content': o.content, 'count': o.count, 'selected': selected}


def _sort_options(choices, options):
    opt = [_dict_of_option(options[i], True) for i in choices]
    for i, o in enumerate(options):
        if i not in choices:
            opt.append(_dict_of_option(o))
    return opt


def vote_detail(request, vote_id):
    vote = Vote.objects.exclude('owner', 'creator', 'modifier').get(pk=vote_id)
    # user_id = str(request.user.id)
    # choices = []
    # for answer in vote.result:
    #     if answer.voter.id == user_id:
    #         choices = answer.choices
    #         break
    # if vote.kind != 'single' and choices:
    #     options = _sort_options(choices, vote.options)
    # else:
    options = [_dict_of_option(o) for o in vote.options]
    # for i in choices:
    #     options[i]['selected'] = True
    data = {
        'destination': '/dsub/vote' + str(vote.id),
        'vote_id': str(vote.id),
        'title': vote.title,
        'start_time': vote.start_time.strftime('%Y-%m-%d %H:%M:%S')
        if vote.start_time else '',
        'type': vote.kind,
        'end_time': vote.end_time.strftime('%Y-%m-%d %H:%M:%S')
        if vote.end_time else '',
        'finished': vote.finished,
        'max_choice': vote.max_choice,
        'min_choice': vote.min_choice,
        'voter_count': vote.voter_count,
        'options': options,
        'message_queue': settings.MESSAGE_QUEUE,
    }
    return HttpResponse(json.dumps(data, ensure_ascii=False))


@authenticated_required
@csrf_exempt
def upload_log(request):
    f = util.get_uploaded_tmpfile(request.FILES['file'])
    user = request.user
    device = user.userprofile.device_id
    try:
        for line in f:
            time, action, resource_id, parameter, result = line.strip().split('|')
            i = time.rfind(':')
            if i:
                time = time[:i]
            UserLog.objects.create(
                user=EmbeddedUser(id=str(user.id), name=user.username),
                device=device,
                action=action,
                resource_id=resource_id,
                parameter=parameter,
                result=result,
                time=datetime.strptime(time, '%Y-%m-%d %H:%M:%S'))
    finally:
        f.close()
    return HttpResponse(status=200)
