#encoding=utf8

import json
from datetime import datetime

from django.http import HttpResponse

from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache

from common import models as common_models, global_def as common_def
from portal import models
from portal import db_util as pdb_util
from portal import util as putil
from wrapper import check_token
import db_util
import client_data

@csrf_exempt
@never_cache
def login(request):
    from django.contrib.auth.forms import AuthenticationForm
    # import sys
    # print >>sys.stderr, 'get:', request.GET.get('username', 'no username'), request.GET.get('password', 'no password'), 'post:', request.POST.get('username', 'no username'), request.POST.get('password', 'no password')
    form = AuthenticationForm(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        profile = user.userprofile
        auth_login(request, user)
        d = {'token': request.session.session_key, 'user_id': user.id, 'user_type': profile.get_usertype()}
        return HttpResponse(json.dumps(d))
    else:
        return HttpResponse(status=501)
        
@check_token
def user_properties(request, token, uid):
    try:
        profile = common_models.UserProfile.objects.select_related('school', 'myclass').get(user__pk=uid)
        age = profile.get_age()
        if age is None:
            age = 0
        data = {
            'user_type': profile.get_usertype(),
            'school_id': profile.school_id,
            'school_name': profile.school and profile.school.name or '',
            'name': profile.user.first_name,
            'sex': profile.get_gender(),
            'age': age,
            'tel': profile.telphone,
            'address': profile.address
            }
        if profile.usertype == common_def.USERTYPE_STUDENT:
            grade = profile.myclass.get_grade()
            data.update({
                'grade_id': grade,
                'grade_name': common_def.get_grade_display(grade),
                'class_id': profile.myclass.id,
                'class_name': profile.myclass.name,
                })
    except User.DoesNotExist:
        data = {}
    return HttpResponse(json.dumps(data, ensure_ascii=False))

@check_token
def course_list(request, token, uid):
    usertype = db_util.get_usertype(uid, request.session)
    if usertype == common_def.USERTYPE_STUDENT:
        courses = db_util.get_student_courses(request.session)
        courses = [{'course_id': c.id, 'course_name': c.course_name} for c in courses]
    elif usertype == common_def.USERTYPE_TEACHER:
        courses = db_util.get_teacher_courselist(uid)
    return HttpResponse(json.dumps(courses, ensure_ascii=False))

@check_token
def courseware_list(request, token, uid):
    usertype = db_util.get_usertype(uid, request.session)
    if usertype == common_def.USERTYPE_TEACHER:
        coursewares = common_models.Courseware.objects.filter(teacher=uid).order_by('course', '-modified_time')
        if 'grade' in request.GET:
            coursewares = coursewares.filter(grade=request.GET['grade'])
        if 'course' in request.GET:
            coursewares = coursewares.filter(course=request.GET['course'])
        if 'book_version' in request.GET:
            coursewares = coursewares.filter(book_provider=request.GET['book_version'])
    elif usertype == common_def.USERTYPE_STUDENT:
        coursewares = db_util.get_student_coursewares(uid, request.session)
        if 'course' in request.GET:
            coursewares = coursewares.filter(course=request.GET['course'])
    else:
        coursewares = []
    db_util.find_new_coursewares(coursewares, [c.id for c in coursewares], uid)
    return HttpResponse(client_data.json_from_courseware(coursewares))

@check_token
def shared_coursewares(request, token, uid, grade, course_id):
    if request.session['user_type'] == common_def.USERTYPE_TEACHER:
        week = None
        date_s = request.GET.get('date', '')
        if date_s:
            try:
                date_s = request.GET['date']
                date = datetime.strptime(date_s, '%Y-%m-%d').date()
                week = putil.weeks_of_semester(date, request.session['semester_start'])            
            except: pass
        coursewares = pdb_util.shared_coursewares(request.user, grade, course_id, week=week)
    else:
        coursewares = []
    json = client_data.json_from_courseware(coursewares)
    return HttpResponse(json)

@csrf_exempt
@check_token
def put_favorite(request, token, uid, type, cid):
    try:
        if type.isdigit():
            db_util.save_favorite_courseware(request.user, type, cid)
        elif type=='huanggang':
            db_util.save_favorie_stuff(request.user, type, request.POST['detail'])
        ret = {'result': 'ok'}
    except db_util.RepeatSave:
        ret = {'result': 'fail', 'message': u'重复收藏'}
    except Exception, e:
        ret = {'result': 'error', 'message': str(e)}
    return HttpResponse(json.dumps(ret, ensure_ascii=False))

@check_token
def get_favorite(request, token, uid, type, course_id):
    ret = []
    try:
        if type=='huanggang':
            stuffs = db_util.read_favorite_stuff(request.user, type)
            for stuff in stuffs:
                ret.append({
                    'id': stuff.id,
                    'type': stuff.type,
                    'detail': json.loads(stuff.detail)
                    })
        else:
            stuffs = db_util.read_favorite_courseware(request.user, type, course_id)
            for stuff in stuffs:
                courseware = stuff.courseware
                courseware.new = False
                courseware.downloaded = False
                ret.append({
                    'id': stuff.id,
                    'type': stuff.type,
                    'courseware': client_data.slice_courseware(courseware)
                    })
    except Exception, e:
        raise e
    return HttpResponse(json.dumps(ret, ensure_ascii=False))

@check_token
def remove_favorite(request, token, uid, fid):
    try:
        f = models.FavoriteStuff.objects.get(pk=fid)
        if f.user == request.user:
            f.delete()
            ret = {'result': 'ok'}
        else:
            ret = {'result': 'fail', 'message': u'您无权删除该收藏'}
    except Exception, e:
        ret = {'result': 'error', 'message': str(e)}
    return HttpResponse(json.dumps(ret, ensure_ascii=False))
    
@check_token    
@csrf_exempt 
def change_password(request, token, uid):
    old_passwd = request.POST['old_passwd']
    new_passwd = request.POST['new_passwd']
    user = request.user
    if user.check_password(old_passwd):
        user.set_password(new_passwd)
        user.save()
        ret = {'result': 'ok'}
    else:
        ret = {'result': 'fail', 'message': u'密码错误！'}
    return HttpResponse(json.dumps(ret, ensure_ascii=False))

@check_token
def get_contacts(request, token, uid, class_id):
    if request.session['user_type'] == common_def.USERTYPE_STUDENT:
        contacts = db_util.get_teachers(class_id, request.GET.get('name'))
    elif request.session['user_type'] == common_def.USERTYPE_TEACHER:
        contacts = db_util.get_students_parents(class_id, request.GET.get('name'))
    else:
        contacts = []
    return HttpResponse(json.dumps(contacts, ensure_ascii=False))
