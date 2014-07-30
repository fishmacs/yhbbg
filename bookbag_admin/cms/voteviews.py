#encoding=utf-8

import json
from datetime import timedelta, datetime

from django.http import HttpResponse, HttpResponseRedirect
#from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
#from django.utils import timezone
from django.conf import settings
from django.forms.formsets import formset_factory

import forms
import voteq

from bookbag.common import models, mongo_models as mmodels
from bookbag.common.mongo_models import Vote
from decorator import has_permission


@has_permission('change_courseware')
def vote_course_list(request):
    qs = models.TeacherClassCourse.objects \
               .select_related('myclass', 'course') \
               .filter(teacher=request.user.id, myclass__is_active=True) \
               .order_by('-myclass__year', 'myclass__id', 'course__id')
    ctx = RequestContext(request, {
        'courses': qs
    })
    return render_to_response('class_course_vote.html', ctx)


@has_permission('change_courseware')
def vote_list(request, course_id):
    if 'search' in request.POST:
        s = request.POST['name']
        page = 1
    elif 'delete' in request.POST:
        ids = request.POST.getlist('selected')
        votes = Vote.objects.filter(id__in=ids)
        for vote in votes:
            if vote.started:
                #vote.end_time = datetime.now()  # timezone.now()
                #vote.finished = True
                vote.deleted = True
                vote.save()
            else:
                vote.delete()
            voteq.send({'command': 'delete_vote',
                        'owner': '%s__%s' % (vote.owner.kind, vote.owner.id),
                        'vote_id': str(vote.id)})
        s = request.POST['name']
        page = request.POST['page']
    else:
        s = ''
        page = request.GET.get('page', 1)
    form = forms.NameForm({'name': s})
    votes = Vote.objects.filter(owner__id=course_id, deleted=False)
    if s:
        votes = votes.filter(title__icontains=s)
    ctx = RequestContext(request, {
        'votes': votes.order_by('-start_time'),
        'form': form,
        'page': page,
        'course_id': course_id,
    })
    return render_to_response('vote_list.html', ctx)


@has_permission('change_courseware')
def vote_detail(request, vote_id):
    vote = Vote.objects.get(pk=vote_id)
    if vote.finished:
        choices = [(o.content, o.count) for o in vote.options]
    else:
        choices = [(o.content, 0) for o in vote.options]
    mqcfg = settings.MESSAGE_QUEUE
    vote_data = {'server': {'url': mqcfg['ws_url'],
                            'user': mqcfg['username'],
                            'password': mqcfg['password']},
                 'choices': choices}
    ctx = RequestContext(request, {
        'vote': vote,
        'voter_count': vote.voter_count if vote.finished else 0,
        'course_id': vote.owner.id,
        'vote_data': json.dumps(vote_data),
    })
    return render_to_response('vote_detail.html', ctx)


@has_permission('change_courseware')
def vote_edit(request, vote_id):
    vote = Vote.objects.get(pk=vote_id)
    course_id = vote.owner.id
    vote1 = {'options': []}
    if 'submit' in request.POST:
        errors, formset = _process_vote_form(request.POST, vote1)
        start_time, end_time = formset
        if not errors:
            _edit_vote(vote, request.user, vote1)
            return HttpResponseRedirect('/vote/list/%s/' % vote.owner.id)
        vote = vote1
    else:
        errors = None
        if vote.start_time:
            starttime = vote.start_time
        else:
            starttime = datetime.now().replace(minute=0)
            starttime += timedelta(hours=1)
        if vote.end_time:
            endtime = vote.end_time
        else:
            endtime = datetime.now().replace(hour=12, minute=0)
            endtime += timedelta(1)
        formset = formset_factory(forms.DateTimeForm)({
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-date': starttime.date(),
            'form-0-hour': starttime.hour,
            'form-0-minute': starttime.minute,
            'form-0-manual': not vote.start_time,
            'form-1-date': endtime.date(),
            'form-1-hour': endtime.hour,
            'form-1-minute': endtime.minute,
            'form-1-manual': not vote.end_time,
        })
        start_time, end_time = formset
    ctx = RequestContext(request, {
        'vote': vote,
        'course_id': course_id,
        'option_count': len(vote.options),
        'errors': errors,
        'start_time': start_time,
        'end_time': end_time,
        'formset': formset,
    })
    return render_to_response('vote_edit.html', ctx)


@has_permission('change_courseware')
def vote_add(request, course_id):
    vote = {'kind': 'single',
            'min_choice': 1,
            'max_choice': 4,
            'options': [{}, {}, {}, {}]}
    if 'submit' in request.POST:
        errors, formset = _process_vote_form(request.POST, vote)
        start_time, end_time = formset
        if not errors:
            _add_vote(vote, course_id, request.user)
            return HttpResponseRedirect('/vote/list/%s/' % course_id)
    else:
        errors = None
        now = datetime.now()
        starttime = now + timedelta(hours=1)
        formset = formset_factory(forms.DateTimeForm)({
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 2,
            'form-0-date': starttime.date(),
            'form-0-hour': starttime.hour,
            'form-0-minute': 0,
            'form-0-manual': False,
            'form-1-date': now.date()+timedelta(1),
            'form-1-hour': 12,
            'form-1-minute': 0,
            'form-1-manual': False,
        })
        start_time, end_time = formset
    ctx = RequestContext(request, {
        'new_vote': True,
        'vote': vote,
        'course_id': course_id,
        'option_count': len(vote['options']),
        'errors': errors,
        'start_time': start_time,
        'end_time': end_time,
        'formset': formset,
    })
    return render_to_response('vote_edit.html', ctx)


@has_permission('change_courseware')
def vote_start(request, vid):
    vote = Vote.objects.get(pk=vid)
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
    return HttpResponseRedirect('/vote/list/%s' % vote.owner.id)


@has_permission('change_courseware')
def vote_end(request, vid):
    vote = Vote.objects.get(pk=vid)
    vote.finished = True
    vote.end_time = datetime.now()
    vote.save()
    voteq.send({'command': 'end_vote',
                'owner': '%s__%s' % (vote.owner.kind, vote.owner.id),
                'vote_id': str(vote.id)})
    return HttpResponseRedirect('/vote/list/%s' % vote.owner.id)


def _process_vote_form(reqdata, vote):
    title = reqdata['title']
    errors = {}
    vote['kind'] = reqdata['kind']
    if not title:
        errors['title_error'] = u'请输入投票标题'
    vote['title'] = title
    i = 0
    options = vote['options']
    del(options[:])
    while(True):
        try:
            option = reqdata['option%d' % (i+1)]
        except KeyError:
            break
        else:
            options.append({'content': option})
        i += 1
    option_count = len([o for o in options if o.get('content')])
    if option_count < 2:
        errors['option_error'] = u'请提供至少两个选项'

    max_choice = min(int(reqdata['max_choice']), option_count)
    vote['max_choice'] = max_choice
    vote['min_choice'] = min(int(reqdata['min_choice']), max_choice)

    formset = formset_factory(forms.DateTimeForm, extra=2)(reqdata)
    formset.is_valid()
    start_time = formset[0]
    end_time = formset[1]
    if start_time.cleaned_data['manual']:
        vote['start_time'] = None
    else:
        date = start_time.cleaned_data['date']
        vote['start_time'] = datetime(date.year, date.month, date.day,
                                      int(start_time.cleaned_data['hour']),
                                      int(start_time.cleaned_data['minute']))
    if end_time.cleaned_data['manual']:
        vote['end_time'] = None
    else:
        date = end_time.cleaned_data['date']
        vote['end_time'] = datetime(date.year, date.month, date.day,
                                    int(end_time.cleaned_data['hour']),
                                    int(end_time.cleaned_data['minute']))
    return errors, formset


def _add_vote(vote, course_id, user):
    _, courseid = course_id.split('_')
    course = models.Course.objects.get(pk=courseid)
    Vote.objects.create(
        title=vote['title'],
        kind=vote['kind'],
        min_choice=vote['min_choice'],
        max_choice=vote['max_choice'],
        start_time=vote['start_time'],
        end_time=vote['end_time'],
        owner=mmodels.EmbeddedOwner(id=course_id,
                                    name=course.course_name,
                                    en_name=course.english_name),
        creator=mmodels.EmbeddedUser(id=str(user.id), name=user.username),
        options=[mmodels.Option(content=o['content']) for o in vote['options'] if o['content']])


def _edit_vote(vote, user, new_vote):
    vote.title = new_vote['title']
    vote.kind = new_vote['kind']
    vote.min_choice = new_vote['min_choice']
    vote.max_choice = new_vote['max_choice']
    if not vote.started:
        vote.start_time = new_vote['start_time']
    vote.end_time = new_vote['end_time']
    vote.modifier = mmodels.EmbeddedUser(id=str(user.id), name=user.username)
    vote.modified_time = datetime.now()
    vote.options = [mmodels.Option(content=o['content']) for o in new_vote['options'] if o['content']]
    vote.save()


@has_permission('change_courseware')
def vote_clear(request, vote_id):
    vote = Vote.objects.get(pk=vote_id)
    vote.result = []
    vote.voter_count = 0
    for i in xrange(len(vote.options)):
        vote.options[i].count = 0
    vote.save()
    return HttpResponse(stats=200)
