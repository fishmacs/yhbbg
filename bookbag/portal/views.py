# Create your views here.
#encoding=utf-8

import os
import json
from urlparse import urlparse
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.db import transaction
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.views.decorators.cache import never_cache, cache_page
from django.shortcuts import render_to_response
from django.utils.encoding import smart_str
from django.utils.translation import check_for_language
from django.utils.http import urlquote
from django.contrib.auth import login, authenticate, logout
from django.core.servers.basehttp import FileWrapper
from django.contrib.auth.decorators import login_required

from common import models, global_def as common_def, image
from common.decorator import json_wrapper
from decorator import authenticated_required
import ware_util
import db_util
import util
import client_data
import coursetree


def _response_set_lang(lang, request, response):
    if lang.startswith('zh'):
        lang = 'zh-cn'
    if lang and check_for_language(lang):
        if hasattr(request, 'session'):
            request.session['django_language'] = lang
        else:
            response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang)
    return response


def _auth(request, device_id, username, password):
    status = 200
    redirect = True
    #if request.user.is_anonymous() or request.user.username != username:
    logout(request)
    need_login = True
    # else:
    #     need_login = False
    user = authenticate(username=username, password=password)
    if user:
        profile = user.get_profile()
        if db_util.need_check_device(user):
            if not profile.device_id:
                p = models.UserProfile.objects.filter(device_id=device_id)
                if not p:
                    profile.device_id = device_id
                    profile.save()
        elif profile.device_id != device_id:
            ware_util.delete_delivered(user)
            profile.device_id = device_id
            profile.save()
        if profile.device_id == device_id:
            if need_login:
                login(request, user)
            mac_addr = request.GET.get('mac', '')
            serial_no = request.GET.get('serial', '')
            if mac_addr or serial_no:
                # if profile.mac_addr != mac_addr or \
                #    profile.serial_no != serial_no:
                #     profile.mac_addr = mac_addr
                #     profile.serial_no = serial_no
                #     profile.save()
                # if there are mac_addr & serial_no, no redirect to /
                redirect = False
        else:
            status = 502
    else:
        status = 501
    # else:
    #     # still in last session, but another user login with the same username
    #     user = request.user
    #     profile = user.get_profile()
    #     if not profile.device_id:
    #         profile.device_id = device_id;
    #         profile.save()
    #     elif profile.device_id != device_id:
    #         if db_util.need_check_device(user):
    #             status = 502
    #         else:
    #             ware_util.delete_delivered(user)
    #             profile.device_id = device_id
    #             profile.save()
    return status, redirect


@never_cache
def start_page(request, lang, device_id, username, password):
    status, redirect = _auth(request, device_id, username, password)
    if status == 200:
        app = request.GET.get('app', '')
        if app:
            profile = request.user.get_profile()
            if profile.app_version != app:
                profile.app_version = app
                profile.save()
        if request.GET.get('clear', '') == '1':
            ware_util.set_courseware_undownloaded(request.user)
        if redirect:
            response = HttpResponseRedirect('/')
            return response  # _response_set_lang(lang, request, response)
    return HttpResponse(status=status)


@csrf_protect
@never_cache
def login_page(request):
    from django.contrib.auth.forms import AuthenticationForm

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            #request.session['previous_login'] = request.user.previous_login
            response = HttpResponseRedirect('/')
            #response.set_cookie('sso_token', '1234')
            return response
    else:
        form = AuthenticationForm(request)
    ctx = RequestContext(request, {
        'form': form})
    return render_to_response('login.html', ctx)


@csrf_exempt
@never_cache
def login_tst(request):
    from django.contrib.auth.forms import AuthenticationForm

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            #request.session['previous_login'] = request.user.previous_login
            response = HttpResponseRedirect('/')
            #response.set_cookie('sso_token', '1234')
            return response
    else:
        form = AuthenticationForm(request)
    ctx = RequestContext(request, {
        'form': form})
    return render_to_response('login.html', ctx)


def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/login/')

# def _get_course_list(user, session):
#     #course_update_time = session.get('course_update_time')
#     # if not course_update_time or \
#     #    time.time()-course_update_time>settings.COURSE_LIST_TIMEOUT or \
#     #    models.Course.objects.filter(modified_time__gt=datetime.fromtimestamp(course_update_time)):
#     courses = db_util.courses_of_user(user, session)
#     course_ids = []
#     # else:
#     #     course_ids = session['course_ids']
#     #     courses = models.Course.objects.filter(id__in=course_ids).order_by('course_id')
#     course_list = []
#     course_dict = {}
#     for course in courses:
#         course_ids.append(course.id)
#         course_list.append(course)
#         course_dict[course.id] = course
#         course.coursewares = {}
#         course.newwares = {}
#     # if not course_ids:
#     #     course_ids = course_dict.keys()
#     #     session['course_ids'] = course_ids
#     #     session['course_update_time'] = time.time()
#     return course_list, course_dict, course_ids


@login_required
def course_page(request):
    user = request.user
    course_list, courseware_list = db_util.course_courseware_list(user, request.session)
    kind = request.META['HTTP_HOST'].split('.')[0]
    plist_url = 'itms-services://?action=download-manifest&url=http://update.bookbag.palmtao.com:4000/bupt-%s-ent.plist' % kind
    ctx = RequestContext(request, {
        'courses': course_list,
        'username': user.first_name,
        'json_wares': client_data.json_from_courseware(courseware_list),
        'update_url': plist_url
        })
    return render_to_response('course_page2.html', ctx)


@authenticated_required
def all_data0(request):
    week = None
    date_s = request.GET.get('date', '')
    if date_s:
        try:
            date_s = request.GET['date']
            date = datetime.strptime(date_s, '%Y-%m-%d').date()
            week = util.weeks_of_semester(date,
                                          request.session['semester_start'])
        except:
            pass
    try:
        clss = int(request.GET['class'])
    except:
        clss = -1
    course_list, _ = db_util.course_courseware_list(request.user, request.session, week=week, clss=clss)
    jsd = client_data.json_from_course(course_list)
    return HttpResponse(jsd)


@authenticated_required
@cache_page(120)
def all_data(request, _):
    week = None
    date_s = request.GET.get('date', '')
    if date_s:
        try:
            date_s = request.GET['date']
            date = datetime.strptime(date_s, '%Y-%m-%d').date()
            week = util.weeks_of_semester(date,
                                          request.session['semester_start'])
        except:
            pass
    try:
        clss = int(request.GET['class'])
    except:
        clss = -1
    course_list, _ = db_util.course_courseware_list(request.user, request.session, week=week, clss=clss)
    jsd = client_data.json_from_course(course_list)
    return HttpResponse(jsd)


def _file_exists(path):
    if not os.path.exists(path):
        ### some time can not find the file until list the dir(system time difference of mount?)
        import sys
        print >>sys.stderr, 'file not found bug: ', path
        return os.path.basename(path) in os.listdir(os.path.dirname(path))
    return True


def _get_courseware(request):
    bookid = request.GET['bookid']
    raw = models.Courseware.objects.get(id=bookid)
    try:
        courseware = ware_util.get_newest_courseware(raw, request.user)
    except models.UserCourseware.DoesNotExist:
        courseware = ware_util.deliver_user_courseware(request.user, raw)
    if courseware:
        if not courseware.url:
            courseware.url = ware_util.redeliver(request.user, raw)
            courseware.save()
        if _file_exists(courseware.url) and \
           os.path.getmtime(courseware.url) > os.path.getmtime(raw.outpath) or \
           ware_util.redeliver(request.user, raw):
            return dlfunc(courseware.url)
    return HttpResponse(status=500)


def _get_courseware_pdf(request):
    bookid = request.GET['bookid']
    courseware = models.Courseware.objects.get(id=bookid)
    delivered, _ = models.UserCourseware.objects.get_or_create(user=request.user, raw=courseware)
    pdf_path = util.pdf_from_mrf(bookid, courseware.outpath)
    if _file_exists(pdf_path):
        delivered.download_time = datetime.now()
        delivered.save()
        return dlfunc(pdf_path)
    return HttpResponse(status=500)


def _download(path):
    f = open(path, 'rb')
    response = HttpResponse(FileWrapper(f),
                            content_type='application/octet-stream')
    response['Content-Disposition'] = 'attachment; filename=%s' \
                                      % (urlquote(os.path.basename(path)))
    f.seek(0, 2)
    response['Content-Length'] = f.tell()
    f.seek(0)
    return response


# x-sendfile
def _download_xsend(path):
    response = HttpResponse(mimetype='application/force-download')
    response['Content-Disposition'] = 'attachment; filename=%s' \
                                      % (urlquote(os.path.basename(path)))
    response['X-Sendfile'] = smart_str(path)
    return response

dlfunc = settings.XSEND_ON and _download_xsend or _download

dl_table = {
    'mrf': _get_courseware,
    'pdf': _get_courseware_pdf,
}


@authenticated_required
def getfile(request):
    filetype = request.GET['type']
    try:
        return dl_table[filetype](request)
    except KeyError:
        return HttpResponse(status=405)


def get_course_image(request, id):
    course = models.Course.objects.get(pk=id)
    image.prepare_image(course.image, common_def.COURSE_IMAGE_SIZE)
    return dlfunc(course.image.path)


def get_courseware_image(request, id):
    courseware = models.Courseware.objects.get(pk=id)
    image.prepare_image(courseware.image, common_def.COURSEWARE_IMAGE_SIZE)
    return dlfunc(courseware.image.path)


@authenticated_required
@transaction.commit_on_success
def download_ok(request, courseware_id):
    is_new, delivered = db_util.is_new_courseware(courseware_id, request.user)
    delivered.download_time = datetime.now()
    delivered.save()
    if is_new:
        profile = request.user.userprofile
        profile.newware_count -= 1
        profile.save()
    return HttpResponse('ok')


def offline_timeout(request):
    try:
        val = models.MiscConfig.objects.get(pk='offline_timeout').conf_val
    except models.MiscConfig.DoesNotExist:
        val = settings.DEFAULT_OFFLINE_TIMEOUT
    return HttpResponse(val)

msg_404 = {
    'default': (u'没有找到您请求的页面...',),
    'courseware': (u'您请求的课件暂时不可用，请稍后再试',),
}


# def page_not_found(request):
#     referer = request.META.get('HTTP_REFERER', 'no referer')
#     msg = msg_404.get(referer, msg_404['default'])
#     ctx = RequestContext(request,
#                          {'msgs': msg})
#     return render_to_response('404.html', ctx)


# def server_error(request):
#     return render_to_response('500.html',
#                               RequestContext(request, {}))


# def _error_page(request, errmsg):
#     ctx = RequestContext(request, {
#         'errmsg': errmsg
#         })
#     return render_to_response('500.html', ctx)


@authenticated_required
@csrf_exempt
def change_password(request):
    user = request.user
    #username = request.POST['username']
    try:
        old_passwd = request.POST['old_password']
        new_passwd = request.POST['new_passwordd']
    except Exception:
        return HttpResponse(status=400)
    else:
        if user.check_password(old_passwd):
            user.set_password(new_passwd)
            user.save()
            return HttpResponse(status=200)
        return HttpResponse(status=501)


@authenticated_required
def other_data(request, grade, course_id):
    week = None
    date_s = request.GET.get('date', '')
    if date_s:
        try:
            date_s = request.GET['date']
            date = datetime.strptime(date_s, '%Y-%m-%d').date()
            week = util.weeks_of_semester(date,
                                          request.session['semester_start'])
        except:
            pass
    coursewares = db_util.shared_coursewares(request.user, grade,
                                             course_id, week=week)
    jsd = client_data.json_from_courseware1(coursewares)
    return HttpResponse(jsd)


@authenticated_required
def user_information(request):
    return HttpResponse(client_data.json_from_user(request.user))


@authenticated_required
def course_schedule(request):
    schedule = db_util.get_course_schedule(request.user)
    return HttpResponse(client_data.json_from_schedule(schedule))


@authenticated_required
def contacts(request, class_id):
    contacts = db_util.get_user_contacts(request.user, class_id)
    return HttpResponse(json.dumps(contacts, ensure_ascii=False))


@csrf_exempt
def convert_finish(request):
    host = urlparse(settings.DOC_CONVERT_SERVER).hostname
    if host != 'localhost' and host != request.META['REMOTE_ADDR']:
        return HttpResponse(status=403)
    # client_ip = request.META['REMOTE_ADDR']
    # if client_ip != settings.DOC_CONVERT_SERVER:
    #     return _error_page('您无权访问该页面！')
    courseware_id = request.POST['courseware_id']
    errmsg = request.POST['error']
    ware_util.convert_finish(courseware_id, errmsg)
    return HttpResponse('ok')


def school_code(request, school_id=None):
    if school_id:
        school = models.School.objects.get(pk=school_id)
        sd = [{'name': school.name, 'code': school.code}]
    else:
        schools = models.School.objects.filter(is_active=True)
        sd = [{'name': s.name, 'code': s.code} for s in schools]
    return HttpResponse(json.dumps(sd, ensure_ascii=False))


@authenticated_required
@json_wrapper
def course_tree(request, course_id, class_id):
    return coursetree.export(course_id, class_id)
    