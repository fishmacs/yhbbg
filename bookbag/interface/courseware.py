#encoding=utf-8

'''
Created on 2012-11-27

@author: zw
'''

import sys
import os
import re
import json
import shutil
import uuid
import urllib
from urlparse import urlparse
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse  # , HttpResponseRedirect
#from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.contrib.auth.models import User

from common import models, course_ware, global_def as common_def
from portal import views as pv
from wrapper import check_token
import forms
import util
import log
import db_util
import palmtao


def _error_page(request, errmsg):
    ctx = RequestContext(request, {
        'errmsg': errmsg
        })
    return render_to_response('500.html', ctx)


def _add_courseware(request, token, uid, back_level):
    course_id = request.POST['course_id']
    grade = int(request.POST['grade'])
    classes = db_util.get_teacher_classes(request.user, grade, course_id)
    if not classes:
        return _error_page(request, u'对不起，您无权管理该课程的课件')

    form = forms.CoursewareForm(request.POST, request.FILES)
    form.refresh_choices(classes)
    if form.is_valid():
        path = util.handle_upload(
            form.cleaned_data['file'],
            util.upload_dir(str(request.user.id), course_id))
        courseware = course_ware.create_courseware(
            course_id, grade, request.user, path, form.cleaned_data)
        log.log_addition(request.user, courseware, u'上传课件')
        course_ware.convert_courseware(courseware, False,
                                       request.META['SERVER_PORT'])
        #log.log_change(request.user, courseware, u'格式转换')
        ctx = RequestContext(request, {
            'level': -back_level,
        })
        return render_to_response('history_goto.html', ctx)
    else:
        course_name = request.POST['course_name']
        ctx = RequestContext(request, {
            'courseware': _dummy_courseware(grade, course_id, course_name),
            'form': form,
            'newware': True,
            'back_level': back_level,
            'upload_id': uuid.uuid1().get_hex(),
        })
        return render_to_response('courseware_detail.html', ctx)


def _edit_courseware(courseware, request, classes, back_level):
    form = forms.CoursewareForm(request.POST, request.FILES)
    form.fields['file'].required = False
    #classes = db_util.get_teacher_classes(request.user, courseware.grade, courseware.course_id) 
    form.refresh_choices(classes)
    form.full_clean()
    if form.is_valid():
        f = form.cleaned_data['file']
        if f:
            path = util.handle_upload(f, util.upload_dir(str(request.user.id), str(courseware.course_id)))
            courseware.path = path
            #courseware.state = 0
            courseware.modified_time = datetime.now()
            course_ware.delete_delivered(courseware)
            course_ware.convert_courseware(courseware, False,
                                           request.META['SERVER_PORT'])
        courseware.name = form.cleaned_data['title']
        courseware.book_provider_id = form.cleaned_data['provider']
        courseware.category_id = form.cleaned_data['category']
        courseware.share_level = form.cleaned_data['share']
        courseware.week = form.cleaned_data['week']
        courseware.description = form.cleaned_data['description']
        #courseware.password = form.cleaned_data['password']
        courseware.classes = form.cleaned_data['classes']
        upload_img = form.cleaned_data['image']
        if upload_img:
            #image = courseware.image
            courseware.image = upload_img
            # if image:
            #     try:
            #         os.remove(image.path)
            #     except Exception, e:
            #         print >>sys.stderr, e
        courseware.save()
        log.log_change(request.user, courseware, u'修改课件')
    return form


def _dummy_courseware(grade, course_id, course_name):
    return {
        'id': 0,
        'name': '添加课件',
        'is_converted': False,
        'grade': grade,
        'course_id': course_id,
        'course': {'course_name': course_name},
        }


#@login_required
@check_token
@csrf_exempt
def courseware_add(request, token, uid, grade, course_id):
    course = models.Course.objects.get(pk=course_id)
    grade = int(grade)
    back_level = 1
    if 'add' in request.POST:
        back_level = int(request.POST['back_level'])+1
        return _add_courseware(request, token, uid, back_level)
    classes = db_util.get_teacher_classes(request.user, grade, course_id)
    if not classes:
        return _error_page(request, u'对不起，您无权管理 %s 课程的课件' % course.course_name)
    courseware = _dummy_courseware(grade, course_id, course.course_name)
    form = forms.CoursewareForm(initial={
        'classes': [c[0] for c in classes],
        'share': common_def.SHARE_LEVEL_SCHOOL})
    form.refresh_choices(classes)
    next_url = request.META.get('HTTP_REFERER', 'no referer')
    print >>sys.stderr, "courseware_add next: ", next_url
    ctx = RequestContext(request, {
        'token': token,
        'uid': uid,
        'courseware': courseware,
        'form': form,
        'newware': True,
        'back_level': back_level,
        'upload_id': uuid.uuid1().get_hex(),
    })
    return render_to_response('courseware_detail.html', ctx)


#@login_required
@check_token
@csrf_exempt
def courseware_edit(request, token, uid, courseware_id):
    back_level = 1
    try:
        courseware = models.Courseware.objects.select_related('book_provider', 'category', 'course').get(id=courseware_id)
        classes = db_util.get_teacher_classes(request.user, courseware.grade,
                                              courseware.course_id)
        if not classes:
            return _error_page(request,
                               u'对不起，您无权管理 %s 课程的课件'
                               % courseware.course_name)
        if 'edit' in request.POST:
            back_level = int(request.POST['back_level']) + 1
            form = _edit_courseware(courseware, request, classes, back_level)
            if form.is_valid():
                ctx = RequestContext(request, {
                    'level': -back_level,
                    })
                return render_to_response('history_goto.html', ctx)
        else:
            data = {
                'title': courseware.name,
                #'grade': courseware.grade,
                'provider': courseware.book_provider_id,
                'category': courseware.category_id,
                'description': courseware.description,
                'share': courseware.share_level,
                'week': courseware.week,
                'classes': db_util.get_courseware_classes(courseware),
            }
            form = forms.CoursewareForm(data, {
                'file': os.path.basename(courseware.path)
            })
            form.refresh_choices(classes)
        form.files['file'] = os.path.basename(courseware.path)
        if hasattr(courseware.image, 'path'):
            form.files['image'] = os.path.basename(courseware.image.path)
    except palmtao.LicenseException, e:
        return e.response
    action_name, action_url = courseware.next_action()
    action_url = re.sub('(.+)/(\d+)/$', '/interface\\1/%s/%s/\\2/'
                        % (token, uid), action_url)
    next_url = request.META.get('HTTP_REFERER', 'no referer')
    print >>sys.stderr, "courseware_add next: ", next_url
    ctx = RequestContext(request, {
        'courseware': courseware,
        'form': form,
        'newware': False,
        'action_name': action_name,
        'action_url': action_url,
        'back_level': back_level,
        'upload_id': uuid.uuid1().get_hex(),
    })
    return render_to_response('courseware_detail.html', ctx)


#@login_required
@check_token
def courseware_delete(request, token, uid, courseware_id):
    try:
        courseware = models.Courseware.objects.get(pk=courseware_id)
        if not db_util.is_course_managable_by(courseware.grade,
                                              courseware.course_id,
                                              request.user):
            ret = {'result': 'fail', 'message': u'对不起，您无权管理该课程的课件'}
        else:
            course_ware.delete_courseware(courseware)
            log.log_deletion(request.user, courseware, u'删除课件')
            ret = {'result': 'ok'}
    except Exception, e:
        ret = {'result': 'error', 'message': str(e)}
    return HttpResponse(json.dumps(ret, ensure_ascii=False))


#@login_required
@check_token
def courseware_convert(request, token, uid, courseware_id):
    try:
        _set_backurl(courseware_id)
        courseware = models.Courseware.objects.get(pk=courseware_id)
        if 'recovert' in request.GET:
            courseware.modified_time = datetime.now()
            reconvert = True
        else:
            reconvert = False
        course_ware.convert_courseware(courseware, reconvert,
                                       request.META['SERVER_PORT'])
        log.log_change(request.user, courseware, u'格式转换')
        ret = {'result': 'ok'}
    except Exception, e:
        ret = {'result': 'error', 'message': str(e)}
    return HttpResponse(json.dumps(ret, ensure_ascii=False))


#@login_required
@check_token
def courseware_deliver(request, token, uid, courseware_id):
    try:
        courseware = models.Courseware.objects.get(pk=courseware_id)
        course_ware.deliver_courseware(courseware)
        log.log_change(request.user, courseware, u'分发课件')
        ret = {'result': 'ok'}
    except Exception, e:
        ret = {'result': 'error', 'message': str(e)}
    return HttpResponse(json.dumps(ret, ensure_ascii=False))


#@login_required
@check_token
def courseware_undeliver(request, token, uid, courseware_id):
    try:
        courseware = models.Courseware.objects.get(pk=courseware_id)
        course_ware.undeliver_courseware(courseware)
        log.log_change(request.user, courseware, u'取消分发')
        ret = {'result': 'ok'}
    except Exception, e:
        ret = {'result': 'error', 'message': str(e)}
    return HttpResponse(json.dumps(ret, ensure_ascii=False))


@csrf_exempt
def convert_finish(request):
    host = urlparse(settings.DOC_CONVERT_SERVER).hostname
    if host != 'localhost' and host != request.META['REMOTE_ADDR']:
        return HttpResponse(status=403)
    courseware_id = request.POST['courseware_id']
    errmsg = request.POST['error']
    course_ware.convert_finish(courseware_id, errmsg)
    backurl = _get_backurl(courseware_id)
    if backurl:
        urllib.urlopen('%s?status=%s' % (backurl, errmsg and 'F' or 'S'))
    return HttpResponse('ok')


def courseware_state(request, courseware_id):
    courseware = models.Courseware.objects.get(pk=courseware_id)
    return HttpResponse(courseware.state)


@check_token
def courseware_download(request, token, uid):
    return pv.getfile(request)


def upload_progress(request, upload_id):
    key = 'upload_id:' + upload_id
    d = cache.get(key)
    if d is None:
        d = []
    return HttpResponse(json.dumps(d))


@csrf_exempt
def upload_yu(request):
    data = json.loads(request.REQUEST['data'])
    course = models.Course.objects.get(course_name=data['course'])
    user = User.objects.get(username=data['username'])
    try:
        category = models.CoursewareCategory.objects.get(name_ch=data['category'])
        category = category.id
    except:
        category = 3
    classes = models.TeacherClassCourse.objects.filter(teacher=user,
                                                       course=course)
    filename = os.path.basename(data['path'])
    (title, _,) = os.path.splitext(filename)
    path = os.path.join(util.upload_dir(str(user.id), str(course.id)), filename)
    others = {'title': title,
              'provider': 1,
              'category': category,
              'share': 6,
              'week': data['lesson_count'],
              'description': '',
              'image': '',
              'classes': [c.myclass_id for c in classes]}
    shutil.copy(data['path'], path)
    courseware = course_ware.create_courseware(course.id, data['grade'],
                                               user, path, others)
    course_ware.convert_courseware(courseware, False,
                                   request.META['SERVER_PORT'])
    params = [('coursename', course.course_name),
              ('coursename_en', course.english_name),
              ('courseid', str(course.id)),
              ('category', data['category']),
              ('category_id', str(category)),
              ('category_name', data['category']),
              ('category_name_en', ''),
              ('bookname', courseware.name),
              ('bookid', str(courseware.id)),
              ('password', ''),
              ('type', 'mrf')]
    _set_backurl(str(courseware.id), data['backurl'])
    return HttpResponse('https://k12.telecomedu.com/dl/getfile/?' + '&'.join(
        ['='.join([k, v]) for (k, v,) in params]))


def _get_backurl(courseware_id):
    try:
        with open('/tmp/yuchengwu_backurl_' + courseware_id, 'r') as f:
            return f.read().strip()
    except:
        pass


def _set_backurl(courseware_id, url=None):
    try:
        if url:
            with open('/tmp/yuchengwu_backurl_' + courseware_id, 'w') as f:
                f.write(url)
        else:
            os.remove('/tmp/yuchengwu_backurl_' + courseware_id)
    except:
        pass
