#encoding=utf-8

'''
Created on 2012-11-27

@author: zw
'''

import os
import json
import uuid
from urlparse import urlparse
from datetime import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.core.cache import cache

from bookbag.common import models, course_ware, global_def as common_def
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

@login_required
def coursewares(request, course_id, grade):
    grade = int(grade)
    course = models.Course.objects.get(pk=course_id)
    #course.course_name = common_def.get_grade_display(grade)+course.course_name
    if not db_util.is_course_managable_by(grade, course_id, request.user):
        return _error_page(request, u'对不起，您无权管理 %s%s 课程' % (common_def.get_grade_display(grade), course.course_name))
    if request.POST.has_key('delete'):
        for id in request.POST.getlist('selected_courseware'):
            courseware = models.Courseware.objects.get(id=id)
            course_ware.delete_courseware(courseware)
            log.log_deletion(request.user, courseware, u'删除课件')
    coursewares = course_ware.coursewares_of_course(course_id, grade, user=request.user).order_by('-id')
    ctx = RequestContext(request, {
        'course': course,
        'grade': grade, 
        'coursewares': coursewares,
        'selected': 'selected_courseware'
        })
    return render_to_response('courseware_page.html', ctx)

def _add_courseware(request):
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
        return HttpResponseRedirect('/coursewares/%d/%d/' % (int(course_id), grade))
    else:
        course_name = request.POST['course_name']
        ctx = RequestContext(request, {
            'courseware': _dummy_courseware(grade, course_id, course_name),
            'form': form,
            'newware': True,
            'upload_id': uuid.uuid1().get_hex(),
            })
        return render_to_response('courseware_detail.html', ctx)
    
def _edit_courseware(courseware, request, classes):
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
            courseware.state = common_def.COURSEWARE_STATE_WAITING
            courseware.modified_time = datetime.now()
            course_ware.delete_delivered(courseware)
        courseware.name = form.cleaned_data['title']
        courseware.book_provider_id = form.cleaned_data['provider']
        courseware.category_id = form.cleaned_data['category']
        courseware.share_level = form.cleaned_data['share']
        courseware.week = form.cleaned_data['week']
        courseware.description = form.cleaned_data['description']
        courseware.password = form.cleaned_data['password']
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

@login_required
def courseware_detail(request, courseware_id):
    try:
        if request.method == 'GET' and courseware_id == '0':
            grade = int(request.GET['grade'])
            course_id = request.GET['course_id']
            classes = db_util.get_teacher_classes(request.user, grade, course_id)
            course_name = request.GET['course_name']
            if not classes:
                return _error_page(request, u'对不起，您无权管理 %s 课程的课件' % course_name)
            courseware = _dummy_courseware(grade, course_id, course_name)
            form = forms.CoursewareForm(initial={'classes': [c[0] for c in classes], 'share': common_def.SHARE_LEVEL_SCHOOL})
            form.refresh_choices(classes)   
            newware = True
        elif request.POST.has_key('add'):
            return _add_courseware(request)
        else:
            courseware = models.Courseware.objects.select_related('book_provider', 'category', 'course').get(id=courseware_id)
            newware = False
            classes = db_util.get_teacher_classes(request.user, courseware.grade, courseware.course_id)
            if not classes:
                return _error_page(request, u'对不起，您无权管理 %s 课程的课件' % courseware.course_name)
            if request.POST.has_key('edit'):
                form = _edit_courseware(courseware, request, classes)
            elif request.POST.has_key('delete'):
                log.log_deletion(request.user, courseware, u'删除课件')
                course_ware.delete_courseware(courseware)
                return HttpResponseRedirect('/coursewares/%d/%d/' % (courseware.course_id, courseware.grade))
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
                form = forms.CoursewareForm(data, {'file': os.path.basename(courseware.path),})
                form.refresh_choices(classes)
            form.files['file'] = os.path.basename(courseware.path)
            if hasattr(courseware.image, 'path'):
                form.files['image'] = os.path.basename(courseware.image.path)
    except palmtao.LicenseException, e:
        return e.response
    ctx = RequestContext(request, {
        'courseware': courseware,
        'form': form,
        'newware': newware,
        'upload_id': uuid.uuid1().get_hex(),
        })
    return render_to_response('courseware_detail.html', ctx)

@login_required
def courseware_convert(request, courseware_id):
    courseware = models.Courseware.objects.get(pk=courseware_id)
    if request.GET.has_key('reconvert'):
        courseware.modified_time = datetime.now()
        reconvert = True
    else:
        reconvert = False
    course_ware.convert_courseware(courseware, reconvert, request.META['SERVER_PORT'])
    log.log_change(request.user, courseware, u'格式转换')
    if request.GET.has_key('ajax'):
        return HttpResponse('')
    else:
        next_url = request.META.get('HTTP_REFERER', '')
        if not next_url:
            next_url = '/coursewares/%d/%d/' % (courseware.course_id, courseware.grade)
        return HttpResponseRedirect(next_url)

@login_required
def courseware_deliver(request, courseware_id):
    courseware = models.Courseware.objects.get(pk=courseware_id)
    if courseware.state == common_def.COURSEWARE_STATE_CONVERTED:
        course_ware.deliver_courseware(courseware)
        log.log_change(request.user, courseware, u'分发课件')
    next_url = request.META.get('HTTP_REFERER', '')
    if not next_url:
        next_url = '/coursewares/%d/%d/' % (courseware.course_id, courseware.grade)
    return HttpResponseRedirect(next_url)

@login_required
def courseware_undeliver(request, courseware_id):
    courseware = models.Courseware.objects.get(pk=courseware_id)
    course_ware.undeliver_courseware(courseware)
    log.log_change(request.user, courseware, u'取消分发')
    next_url = request.META.get('HTTP_REFERER', '')
    if not next_url:
        next_url = '/coursewares/%d/%d/' % (courseware.course_id, courseware.grade)
    return HttpResponseRedirect(next_url)
    
@csrf_exempt
def convert_finish(request):
    host = urlparse(settings.DOC_CONVERT_SERVER).hostname
    if host == 'localhost':
        host = '127.0.0.1'
    if host != request.META['REMOTE_ADDR']:
        print request.META['REMOTE_ADDR']
        return _error_page(request, '您无权访问该页面！')
    # client_ip = request.META['REMOTE_ADDR']
    # if client_ip != settings.DOC_CONVERT_SERVER:
    #     return _error_page('您无权访问该页面！')
    courseware_id = request.POST['courseware_id']
    errmsg = request.POST['error']
    course_ware.convert_finish(courseware_id, errmsg)
    return HttpResponse('ok')

def courseware_state(request, courseware_id):
    courseware = models.Courseware.objects.get(pk=courseware_id)
    state = courseware.state_str()
    reconvertable = courseware.reconvertable()
    try:
        action, url = courseware.next_action()
        return HttpResponse('%s,%s,%s,%d' % (state, action, url, reconvertable))
    except:
        pass
    return HttpResponse('%s,%d' % (state, reconvertable))

def upload_progress(request, upload_id):
    key = 'upload_id:' + upload_id
    d = cache.get(key)
    if d is None:
        d = []
    return HttpResponse(json.dumps(d))