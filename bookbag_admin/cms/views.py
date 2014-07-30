#encoding=utf-8

import sys
import json

from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.admin.models import LogEntry
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db import transaction
from django.db import IntegrityError

from bookbag.common import models, global_def as common_def, util as common_util
import forms
import util
import log
import db_util
import signals
import cache
from decorator import has_any_permission, has_permission

signals.connect_login()


@login_required
def main_page(request):
    #user_type = request.session['user_type']
    #nextpage = user_type==common_def.USERTYPE_TEACHER and course_page or menu_page
    return menu_page(request)


@has_permission('change_courseware')
def course_page(request):
    courses = db_util.courses_of_teacher(request.user)
    ctx = RequestContext(request, {
        'courses': courses
        })
    return render_to_response('course_page.html', ctx)

def logout_page(request):
    logout(request)
    return HttpResponseRedirect('/')

@login_required
def menu_page(request):
    ctx = RequestContext(request, {'region': request.session.get('region')})
    return render_to_response('menu.html', ctx)

@has_permission('change_region')
def region_list(request):
    if request.POST.has_key('search'):
        form = forms.SearchRegionForm(request.POST)
        if form.is_valid():
            s = form.cleaned_data['name']
            t = form.cleaned_data['kind']
        else:
            s = request.POST.get('name', '')
            t = request.POST.get('kind', 'name')
        page = 1
    elif request.POST.has_key('delete'):
        ids = request.POST.getlist('selected')
        regions = models.Region.objects.select_for_update().filter(id__in=ids)
        for region in regions:
            log.log_deletion(request.user, region, u'删除区域')
        regions.update(is_active=False)
        s = request.POST['find']
        t = request.POST['kind']
        page = request.POST['page']
    else:
        s = ''
        t = 'name'
        page = '1'
    form = forms.SearchRegionForm(initial={'name': s, 'kind': t})
    regions = db_util.search_region(s, t)
    ctx = RequestContext(request, {
        'regions': regions,
        'form': form,
        'search': s,
        'search_type': t,
        'page': page,
    })
    return render_to_response('region_list.html', ctx)

@has_permission('change_region')
def region_add(request):
    if request.POST.has_key('add'):
        form = forms.RegionForm(request.POST)
        if form.is_valid():
            region = models.Region.objects.create(
                name=form.cleaned_data['name'],
                code=form.cleaned_data['code'])
            log.log_addition(request.user, region, u'添加区域')
            return HttpResponseRedirect('/region/list/')
    else:
        form = forms.RegionForm()
    ctx = RequestContext(request, {'form': form})
    return render_to_response('change_region.html', ctx)
    
@has_permission('change_region')
def region_edit(request, region_id):
    region = models.Region.objects.get(pk=region_id)
    if request.POST.has_key('edit'):
        form = forms.RegionForm(request.POST)
        if form.is_valid():
            region.name = form.cleaned_data['name']
            region.code = form.cleaned_data['code']
            region.save()
            log.log_change(request.user, region, u'修改区域')
            return HttpResponseRedirect('/region/list/')
    elif request.POST.has_key('delete'):
        region.is_active=False
        region.save()
        log.log_deletion(request.user, region, u'删除区域')
        return HttpResponseRedirect('/region/list/')
    else:
        form = forms.RegionForm(instance=region)
    ctx = RequestContext(request, {'form': form, 'region': region})
    return render_to_response('change_region.html', ctx)

@has_permission('change_course')
def course_list(request):
    if request.POST.has_key('search'):
        form = forms.SearchCourseForm(request.POST)
        if form.is_valid():
            s = form.cleaned_data['course']
            t = form.cleaned_data['type']
        else:
            s = request.POST.get('course', '')
            t = request.POST.get('type', 'name')
        page = 1
    elif request.POST.has_key('delete'):
        ids = request.POST.getlist('selected')
        #models.Course.objects.filter(id__in=ids).delete()
        courses = models.Course.objects.filter(id__in=ids)
        for course in courses:
            log.log_deletion(request.user, course, u'删除课程')
        courses.delete()
        s = request.POST['find']
        t = request.POST['type']
        page = request.POST['page']
    else:
        s = request.GET.get('search', '')
        t = request.GET.get('type', 'name')
        page = request.GET.get('page', '1')
    form = forms.SearchCourseForm({'course': s, 'type': t})
    courses = db_util.search_course(s, t)
    ctx = RequestContext(request, {
        'courses': courses,#.order_by('id'),
        'form': form,
        'course': s,
        'type': t,
        'page': page
        })
    return render_to_response('course_list.html', ctx)

@has_permission('change_course')
def add_course(request):
    if request.POST.has_key('add'):
        form = forms.CourseForm(request.POST, request.FILES)
        if form.is_valid():
            course = form.save()
            log.log_addition(request.user, course, u'添加课程')
            return HttpResponseRedirect('/course/list/')
    else:
        form = forms.CourseForm()
    ctx = RequestContext(request, {
        'form': form,
        })
    return render_to_response('change_course.html', ctx)
    #return HttpResponseRedirect('/raw_courses?page=%s&search=%s&type=%s' %(
    #    request.POST['page'], request.POST['find'], request.POST['type']))

@has_permission('change_course')
def edit_course(request):
    if request.POST.has_key('edit'):
        cid = request.POST['course_id']
        course = models.Course.objects.get(pk=cid)
        form = forms.CourseForm(request.POST, request.FILES, instance=course)
        if form.is_valid():
            form.save()
            log.log_change(request.user, course, u'修改课程')
            return HttpResponseRedirect('/course/list/')
    elif request.POST.has_key('delete'):
        cid = request.POST['course_id']
        course = models.Course.objects.get(pk=cid)
        course.delete()
        log.log_deletion(request.user, course, u'删除课程')
        return HttpResponseRedirect('/course/list/')
    else:
        cid = request.GET['course_id']
        course = models.Course.objects.get(pk=cid)
        form = forms.CourseForm(instance=course)
    ctx = RequestContext(request, {
        'form': form,
        'course': course
        })
    return render_to_response('change_course.html', ctx)

@has_permission('change_school')
def school_list(request, region):
    if request.POST.has_key('search'):
        form = forms.SearchSchoolForm(request.POST)
        if form.is_valid():
            s = form.cleaned_data['name']
            t = form.cleaned_data['kind']
        else:
            s = request.POST.get('name', '')
            t = request.POST.get('kind', 'name')
        page = 1
        schools = db_util.search_school(region, s, t)        
    elif request.POST.has_key('delete'):
        ids = request.POST.getlist('selected')
        #models.Course.objects.filter(id__in=ids).delete()
        for id in ids:
            school = models.School.objects.get(id=id)
            log.log_deletion(request.user, school, u'删除学校')
            school.delete()
        s = request.POST['find']
        t = request.POST['kind']
        page = request.POST['page']
        schools = db_util.search_school(region, s, t)
    else:
        s = request.GET.get('search', '')
        t = request.GET.get('kind', 'name')
        page = request.GET.get('page', '1')
        schools = db_util.search_school(region, s, t)
    form = forms.SearchSchoolForm({'name': s, 'kind': t})
    ctx = RequestContext(request, {
        'schools': schools,
        'region': region,
        'form': form,
        'page': page,
        'search': s,
        'search_type': t,
        })
    return render_to_response('school_list.html', ctx)
    
@has_permission('change_school')
def school_add(request, region):
    if request.POST.has_key('add'):
        form = forms.SchoolForm(request.POST)
        form.fields['type'].choices=common_def.get_all_schooltypes()
        cache.set_selected_schooltype(request.user, 'change_school', request.POST['type'], 300)
        if form.is_valid():
            region_name = request.session.get('region_name')
            if not region_name:
                r = models.Region.objects.get(pk=region)
                region_name = r.name
                request.session['region_name'] = region_name
            school = models.School.objects.create(
                name=form.cleaned_data['name'],
                code=form.cleaned_data['code'],
                region_id=region,
                region_name=region_name,
                type=form.cleaned_data['type'],
                description=form.cleaned_data['description'],
                address=form.cleaned_data['address'],
                telphone=form.cleaned_data['telphone'],
                email=form.cleaned_data['email'])
            log.log_addition(request.user, school, u'添加学校')
            return HttpResponseRedirect('/school/list/%s/' % region)
    else:
        t = cache.get_selected_schooltype(request.user, 'change_school')
        form = forms.SchoolForm(initial={'type': t})
        form.fields['type'].choices=common_def.get_all_schooltypes()
    ctx = RequestContext(request, {
        'form': form,
        'region': region,
        })
    return render_to_response('change_school.html', ctx)

@has_permission('change_school')
def school_edit(request, school_id):
    school = models.School.objects.get(pk=school_id)
    if request.POST.has_key('edit'):
        #cid = request.POST['class_id']
        form = forms.SchoolForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            log.log_change(request.user, school, u'修改学校')
            return HttpResponseRedirect('/school/list/%d/' % school.region_id)
    elif request.POST.has_key('delete'):
        #cid = request.POST['class_id']
        school.delete()
        log.log_deletion(request.user, school, u'删除学校')
        return HttpResponseRedirect('/school/list/%d/' % school.region_id)
    else:
        form = forms.SchoolForm(instance=school)
        form.fields['type'].choices=common_def.get_all_schooltypes()
    ctx = RequestContext(request, {
        'form': form,
        'school': school,
        'region': school.region_id,
        })
    return render_to_response('change_school.html', ctx)
    
@has_permission('change_schoolclass')
def class_list(request, grade):
    grades = common_def.get_all_grades(request.session['school_type'], True)
    #grade = int(request.GET.get('grade', '0'))
    grade = int(grade)
    form = None
    if request.POST.has_key('grade'):
        form = forms.GradeForm(request.POST)
        form.fields['grade'].choices = grades
        form.full_clean()
        if form.is_valid():
            grade = int(form.cleaned_data['grade'])
    elif request.POST.has_key('delete'):
        ids = request.POST.getlist('selected')
        for id in ids:
            clas = models.SchoolClass.objects.get(id=id)
            clas.delete()
            log.log_deletion(request.user, clas, u'删除班级')
        cache.clear_grade_classes(request.session['school'], grade)
    # if not grade:
    #     grade = grades[0][0]
    if not form:
        form = forms.GradeForm(initial={'grade': grade})
        form.fields['grade'].choices = grades
    year = common_util.get_grade_year(grade)
    classes = models.SchoolClass.objects.filter(school=request.session['school'], year=year, is_active=True)
    ctx = RequestContext(request, {
        'classes': classes,
        'form': form,
        'grade': grade,
        })
    return render_to_response('class_list.html', ctx)
        
@has_permission('change_schoolclass')
def class_add(request, grade):
    if request.POST.has_key('add'):
        form = forms.ClassForm(request.POST)
        if form.is_valid():
            clas = db_util.create_class(
                form.cleaned_data['name'],
                int(grade), None,
                request.session['school'],
                request.session['school_type'])
            log.log_addition(request.user, clas, u'添加班级')
            cache.clear_grade_classes(request.session['school'], int(grade))
            return HttpResponseRedirect('/class/list/%s/' % grade)
    else:
        form = forms.ClassForm()
    ctx = RequestContext(request, {
        'form': form,
        })
    return render_to_response('change_class.html', ctx)
        
@has_permission('change_schoolclass')
def class_edit(request, class_id):
    if request.POST.has_key('edit'):
        cid = request.POST['class_id']
        cls = models.SchoolClass.objects.get(pk=cid)
        form = forms.ClassForm(request.POST, instance=cls)
        if form.is_valid():
            grade = cls.get_grade()
            form.save()
            log.log_change(request.user, cls, u'修改班级')
            cache.clear_grade_classes(request.session['school'], grade)
            return HttpResponseRedirect('/class/list/%d/' % grade)
    elif request.POST.has_key('delete'):
        cid = request.POST['class_id']
        cls = models.SchoolClass.objects.get(pk=cid)
        for u in cls.userprofile_set.all():
            u.myclass_id = None
            u.save()
        cls.delete()
        log.log_deletion(request.user, cls, u'删除班级')
        cache.clear_grade_classes(request.session['school'], cls.get_grade())
        return HttpResponseRedirect('/class/list/%d/' % cls.get_grade())
    else:
        cls = models.SchoolClass.objects.get(pk=class_id)
        form = forms.ClassForm(instance=cls)
    ctx = RequestContext(request, {
        'form': form,
        'class': cls,
        })
    return render_to_response('change_class.html', ctx)

@has_permission('auth.change_student')
def student_list(request):
    if request.POST:
        s = request.POST['username']
        t = request.POST['kind']
        page = request.POST.get('page', 1)
        if request.POST.has_key('delink'):
            ids = request.POST.getlist('selected')
            for id in ids:
                user = User.objects.get(id=id)
                db_util.delink_device(user)
                #course_ware.delete_coursewares(user)
                log.log_change(request.user, user, u'解除设备绑定')
        elif request.POST.has_key('delete'):
            for id in request.POST.getlist('selected'):
                user = User.objects.get(id=id)
                user.delete()
                log.log_deletion(request.user, user, u'删除用户')
    else:
        s = request.GET.get('username', '')
        t = request.GET.get('kind', 'username')
        page = request.GET.get('page', '1')
    form = forms.UsernameForm({'username': s, 'kind': t})
    profiles = models.UserProfile.objects.select_related('user', 'myclass').filter(usertype=common_def.USERTYPE_STUDENT, school=request.session['school'], user__is_active=True)
    if s:
        if t == 'fullname':
            profiles = profiles.filter(user__first_name__icontains=s)
        else:
            profiles = profiles.filter(user__username__icontains=s)
    ctx = RequestContext(request, {
        'profiles': profiles.order_by('user__username'),
        'form': form,
        'username': s,
        'kind': t,
        'page': page
        })
    return render_to_response('user_list.html', ctx)

@has_permission('auth.change_student')
def student_add(request):
    if request.POST.has_key('add'):
        form = forms.UserForm(request.POST)
        form.fields['grade'].choices = common_def.get_all_grades(request.session['school_type'], prompt=True)        
        form.fields['myclass'].choices = cache.get_grade_classes(request.session['school'], int(request.POST['grade']))
        if form.is_valid():
            uname = form.cleaned_data['username']
            #utype = int(form.cleaned_data['type'])
            with transaction.commit_on_success():
                user = User.objects.create(
                    username=uname,
                    first_name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'])
                user.set_password(form.cleaned_data['password'])
                user.save()
                profile = user.userprofile
                profile.usertype = common_def.USERTYPE_STUDENT
                profile.region_id = request.session['region']
                profile.school_id = request.session['school']
                profile.myclass_id = int(request.POST['myclass'])
                profile.gender = form.cleaned_data['gender']
                profile.birthday = form.cleaned_data['birthday']
                profile.telphone = form.cleaned_data['tel']
                profile.contact = json.dumps({'tel': profile.telphone, 'email': user.email}, ensure_ascii=False)
                profile.save()
                log.log_addition(request.user, user, u'添加用户')
            return HttpResponseRedirect('/student/list/')
    elif request.POST:
        # change grade
        grade = int(request.POST['grade'])
        cache.set_selected_grade(request.user, 'change_student', grade, 300)
        form = forms.UserForm(request.POST)
        form.fields['grade'].choices = common_def.get_all_grades(request.session['school_type'], prompt=True)
        form.fields['myclass'].choices = cache.get_grade_classes(request.session['school'], grade)
        form.errors.clear()        
    else:
        grade = cache.get_selected_grade(request.user, 'change_student')
        form = forms.UserForm(initial={'grade': grade})
        form.fields['grade'].choices = common_def.get_all_grades(request.session['school_type'], prompt=True)
        form.fields['myclass'].choices = cache.get_grade_classes(request.session['school'], grade)
    ctx = RequestContext(request, {
        'form': form,
        })
    return render_to_response('change_user.html', ctx)

@has_permission('auth.change_student')
def student_edit(request):
    if request.POST.has_key('edit'):
        form = forms.UserForm(request.POST)
        form.fields['password'].required = False
        form.fields['password1'].required = False
        form.fields['grade'].choices = common_def.get_all_grades(request.session['school_type'], prompt=True)
        form.fields['myclass'].choices = cache.get_grade_classes(request.session['school'], int(request.POST['grade']))
        uid = request.POST['uid']
        user = User.objects.get(pk=uid)
        if form.is_valid():
            password = form.cleaned_data['password']
            if password:
                user.set_password(password)
            #utype = int(form.cleaned_data['type'])
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['name']
            user.email = form.cleaned_data['email']
            profile = user.userprofile
            #profile.usertype = utype
            profile.gender = form.cleaned_data['gender']
            profile.myclass_id = form.cleaned_data['myclass']#int(request.POST['myclass'])
            profile.birthday = form.cleaned_data['birthday']
            profile.telphone = form.cleaned_data['tel']
            profile.contact = json.dumps({'tel': profile.telphone, 'email': user.email}, ensure_ascii=False)
            with transaction.commit_on_success():
                user.save()
                profile.save()
                log.log_change(request.user, user, u'修改用户')
            return HttpResponseRedirect('/student/list/')
    elif request.POST.has_key('delete'):
        uid = request.POST['uid']
        user = User.objects.get(pk=uid)
        user.delete()
        log.log_deletion(request.user, user, u'删除用户')
        return HttpResponseRedirect('/student/list/')
    elif request.POST:
        # change grade
        uid = request.POST['uid']
        grade = int(request.POST['grade'])
        cache.set_selected_grade(request.user, 'change_student', grade, 300)
        form = forms.UserForm(request.POST)
        form.fields['grade'].choices = common_def.get_all_grades(request.session['school_type'], prompt=True)
        form.fields['myclass'].choices = cache.get_grade_classes(request.session['school'], grade)
        form.errors.clear()        
    else:
        uid = request.GET['uid']
        profile = models.UserProfile.objects.select_related('user', 'myclass').get(user__id=uid)
        grade = profile.myclass.get_grade()
        data = {
            'username': profile.user.username,
            'name': profile.user.first_name,
            #'en_name': user.last_name,
            'gender': profile.gender,
            'grade': grade,
            'myclass': profile.myclass_id,
            'birthday': profile.birthday,
            #'type': profile.usertype,
            }
        form = forms.UserForm(initial=data)
        form.fields['password'].required = False
        form.fields['password1'].required = False
        form.fields['grade'].choices = common_def.get_all_grades(request.session['school_type'], prompt=True)
        form.fields['myclass'].choices = cache.get_grade_classes(request.session['school'], grade)
    ctx = RequestContext(request, {
        'form': form,
        'uid': uid,
        })
    return render_to_response('change_user.html', ctx)


IMPORT_UPPER_LINKS = {
    'teacher': '/teacher/list/',
    'student': '/student/list/',
    }

@has_any_permission('auth.change_student auth.change_teacher')
def import_user(request, usertype):
    errors = None
    upper_link = IMPORT_UPPER_LINKS[usertype]
    if request.POST.has_key('upload'):
        form = forms.UserImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                util.import_user(form.cleaned_data['file'])
                return HttpResponseRedirect(upper_link)
            except Exception, e:
                import traceback
                traceback.print_exc(file=sys.stderr)
                errors = unicode(e).split('\n')
    else:        
        form = forms.UserImportForm()
    ctx = RequestContext(request, {
        'form': form,
        'errors': errors,
        'type': 'import',
        'usertype': usertype,
        })
    return render_to_response('batch_user.html', ctx)

@has_permission('auth.change_student')
def batch_del_user(request):
    errors = None
    if request.POST.has_key('upload'):
        form = forms.UserImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                util.batch_delete(form.cleaned_data['file'])
                return HttpResponseRedirect('/student/list/')
            except Exception, e:
                import traceback
                traceback.print_exc(file=sys.stderr)
                errors = unicode(e).split('\n')
    else:        
        form = forms.UserImportForm()
    ctx = RequestContext(request, {
        'form': form,
        'errors': errors,
        'type': 'delete',
        })
    return render_to_response('batch_user.html', ctx)
    
@has_permission('auth.change_teacher')
def teacher_list(request):
    if request.POST:
        s = request.POST['username']
        t = request.POST['kind']
        page = request.POST.get('page', 1)
        if request.POST.has_key('delink'):
            ids = request.POST.getlist('selected')
            for id in ids:
                user = User.objects.get(id=id)
                db_util.delink_device(user)
                #course_ware.delete_coursewares(user)
                log.log_change(request.user, user, u'解除设备绑定')
        elif request.POST.has_key('delete'):
            for id in request.POST.getlist('selected'):
                user = User.objects.get(id=id)
                user.delete()
                log.log_deletion(request.user, user, u'删除教师')
    else:
        s = request.GET.get('username', '')
        t = request.GET.get('kind', 'fullname')
        page = request.GET.get('page', '1')
    form = forms.UsernameForm({'username': s, 'kind': t})
    profiles = models.UserProfile.objects.select_related('user').filter(usertype=common_def.USERTYPE_TEACHER, school=request.session['school'], user__is_active=True)
    if s:
        if t == 'fullname':
            profiles = profiles.filter(user__first_name__icontains=s)            
        else:
            profiles = profiles.filter(user__username__icontains=s)
    ctx = RequestContext(request, {
        'profiles': profiles.order_by('user__username'),
        'form': form,
        'username': s,
        'kind': t,
        'page': page
        })
    return render_to_response('teacher_list.html', ctx)

@has_permission('auth.change_teacher')
def teacher_add(request):
    if request.POST.has_key('add'):
        form = forms.TeacherForm(request.POST)
        if form.is_valid():
            uname = form.cleaned_data['username']
            with transaction.commit_on_success():
                user = User.objects.create(
                    username=uname, 
                    first_name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'])
                user.set_password(form.cleaned_data['password'])
                user.groups.add(db_util.group_of_usertype(common_def.USERTYPE_TEACHER))
                user.save()
                profile = user.userprofile
                profile.usertype = common_def.USERTYPE_TEACHER
                profile.region_id = request.session['region']
                profile.school_id = request.session['school']
                profile.gender = form.cleaned_data['gender']
                profile.telphone = form.cleaned_data['telphone']
                profile.contact = json.dumps({'tel': profile.telphone, 'email': user.email}, ensure_ascii=False)
                profile.save()
                log.log_addition(request.user, user, u'添加教师')
            return HttpResponseRedirect('/teacher/list/')
    else:
        form = forms.TeacherForm()
    ctx = RequestContext(request, {
        'form': form,
        })
    return render_to_response('change_teacher.html', ctx)

@has_permission("auth.change_teacher")
def teacher_edit(request):
    if request.POST.has_key('edit'):
        form = forms.TeacherForm(request.POST)
        form.fields['password'].required = False
        form.fields['password1'].required = False
        uid = request.POST['uid']
        user = User.objects.get(pk=uid)
        if form.is_valid():
            password = form.cleaned_data['password']
            if password:
                user.set_password(password)
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['name']
            user.email = form.cleaned_data['email']
            profile = user.userprofile
            profile.gender = form.cleaned_data['gender']
            profile.telphone = form.cleaned_data['telphone']
            profile.contact = json.dumps({'tel': profile.telphone, 'email': user.email}, ensure_ascii=False)
            with transaction.commit_on_success():
                user.save()
                profile.save()
            log.log_change(request.user, user, u'修改教师')
            return HttpResponseRedirect('/teacher/list/')
    elif request.POST.has_key('delete'):
        uid = request.POST['uid']
        user = User.objects.get(pk=uid)
        user.delete()
        log.log_deletion(request.user, user, u'删除教师')
        return HttpResponseRedirect('/teacher/list/')
    else:
        uid = request.GET['uid']
        profile = models.UserProfile.objects.select_related('user', 'myclass').get(user__id=uid)
        data = {
            'username': profile.user.username,
            'name': profile.user.first_name,
            #'en_name': user.last_name,
            'gender': profile.gender,
            'email': profile.user.email,
            'telphone': profile.telphone,
            }
        form = forms.TeacherForm(data)
        form.fields['password'].required = False
        form.fields['password1'].required = False
    ctx = RequestContext(request, {
        'form': form,
        'uid': uid,
        })
    return render_to_response('change_teacher.html', ctx)

@has_permission('auth.change_teacher')
@transaction.commit_on_success
def teacher_class_course(request, uid):
    form = None
    if request.POST.has_key('add'):
        grade = int(request.POST['grade'])
        form = forms.ClassCourseForm(request.POST)
        form.set_choices(request.session, grade)
        if form.is_valid():
            for clas in request.POST.getlist('myclass'):
                for course in request.POST.getlist('course'):
                    try:
                        models.TeacherClassCourse.objects.create(
                            teacher_id=uid,
                            myclass_id=clas,
                            course_id=course)
                    except IntegrityError:
                        pass
            teacher = User.objects.get(pk=uid)
            log.log_change(request.user, teacher, u'改变课程设置')
    elif request.POST.has_key('delete'):
        ids = request.POST.getlist('selected')
        models.TeacherClassCourse.objects.filter(id__in=ids).delete()
        teacher = User.objects.get(pk=uid)
        log.log_change(request.user, teacher, u'改变课程设置')
        grade = int(request.POST['grade1'])
    elif request.POST:
        # change grade
        grade = int(request.POST['grade'])
        form = forms.ClassCourseForm(request.POST)
        form.set_choices(request.session, grade)
        form.errors.clear()
    else:
        grade = 0#int(request.GET.get('grade', '0'))
    if not form:
        form = forms.ClassCourseForm({'grade': grade})
        form.set_choices(request.session, grade)
        form.errors.clear()
    qs = models.TeacherClassCourse.objects.select_related('myclass', 'course').filter(teacher=uid, myclass__is_active=True).order_by('-myclass__year', 'myclass__id', 'course__id')
    ctx = RequestContext(request, {
        'form': form,
        'queryset': qs,
        'grade': grade,
        })
    return render_to_response('teacher_class_course.html', ctx)
    
@has_any_permission("auth.change_sysadmin auth.change_regionadmin auth.change_schooladmin")
def admin_list(request):
    if request.POST.has_key('delink'):
        ids = request.POST.getlist('selected')
        for id in ids:
            user = User.objects.get(id=id)
            db_util.delink_device(user)
            #course_ware.delete_coursewares(user)
            log.log_change(request.user, user, u'解除设备绑定')
        s = request.POST['find']
        page = request.POST['page']
    elif request.POST.has_key('delete'):
        for id in request.POST.getlist('selected'):
            user = User.objects.get(id=id)
            user.delete()
            log.log_deletion(request.user, user, u'删除管理员')
        s = request.POST['find']
        page = request.POST['page']
    elif request.POST.has_key('search'):
        form = forms.NameForm(request.POST)
        if form.is_valid():
            s = form.cleaned_data['name']
        else:
            s = request.POST.get('find', '')
        page = 1
    else:
        s = request.GET.get('username', '')
        page = request.GET.get('page', '1')
    form = forms.NameForm({'name': s})
    usertype = request.session['user_type']
    upper_ut = usertype+1 if usertype==common_def.USERTYPE_SYSTEM_ADMIN else usertype
    profiles = models.UserProfile.objects.select_related().filter(usertype__gt=common_def.USERTYPE_TEACHER, usertype__lt=upper_ut, user__is_active=True)
    if s:
        profiles = profiles.filter(user__username__icontains=s)
    ctx = RequestContext(request, {
        'profiles': profiles.order_by('user__username'),
        'form': form,
        'username': s,
        'page': page
        })
    return render_to_response('admin_list.html', ctx)

@has_any_permission("auth.change_sysadmin auth.change_regionadmin auth.change_schooladmin")
def admin_add(request):
    if request.POST:
        form = forms.adminForm(request.user, request.session.get('region'), request.POST)
        if request.POST.has_key('add'):
            if form.is_valid():
                with transaction.commit_on_success():
                    user = User.objects.create(
                        username=form.cleaned_data['username'],
                        first_name=form.cleaned_data['name'],
                        #last_name=form.cleaned_data['en_name'],
                        email=form.cleaned_data['email'],
                        is_staff=True)
                    user.set_password(form.cleaned_data['password'])
                    user.save()
                    profile = user.userprofile
                    profile.usertype = form.cleaned_data['type']
                    user.groups.add(db_util.group_of_usertype(profile.usertype))
                    profile.school_id = form.cleaned_data.get('school')
                    region = form.cleaned_data.get('region')
                    profile.region_id = region if region else request.session['region']
                    profile.save()
                    log.log_addition(request.user, user, u'添加管理员')
                return HttpResponseRedirect('/admin/list/')
        elif request.POST.has_key('type'):
            form.errors.clear()
            #form.password = request.POST['password']
    else:
        form = forms.adminForm(request.user, request.session.get('region'))
    ctx = RequestContext(request, {
        'form': form,
        })
    return render_to_response('change_admin.html', ctx)

@has_any_permission("auth.change_sysadmin auth.change_regionadmin auth.change_schooladmin")
def admin_edit(request):
    if request.POST.has_key('edit'):
        uid = request.POST['uid']
        profile = models.UserProfile.objects.select_related('user').get(user=uid)
        user = profile.user
        form = forms.adminForm1(request.user, profile, request.POST, request.session.get('region'), True)
        if form.is_valid():
            password = form.cleaned_data['password']
            if password:
                user.set_password(password)
            utype = form.cleaned_data['type']
            user.username = form.cleaned_data['username']
            user.first_name = form.cleaned_data['name']
            user.email = form.cleaned_data['email']
            type_change = profile.usertype != utype
            profile.school_id = form.cleaned_data.get('school')
            region = form.cleaned_data.get('region')
            profile.region_id = region if region else request.session['region']
            with transaction.commit_on_success():
                user.save()
                if type_change:
                    user.groups.clear()
                    user.groups.add(db_util.group_of_usertype(utype))
                    profile.usertype = utype
                profile.save()
                log.log_change(request.user, user, u'修改管理员')
            return HttpResponseRedirect('/admin/list/')
    elif request.POST.has_key('delete'):
        uid = request.POST['uid']
        user = User.objects.get(pk=uid)
        user.delete()
        log.log_deletion(request.user, user, u'删除管理员')
        return HttpResponseRedirect('/admin/list/')
    else:
        data = request.POST or request.GET
        uid = data['uid']
        profile = models.UserProfile.objects.select_related('user').get(user=uid)
        user = profile.user
        usertype = request.POST and int(request.POST['type']) or profile.usertype
        data = {
            'username': user.username,
            'name': user.first_name,
            #'en_name': user.last_name,
            'email': user.email,
            'type': usertype,
            }
        if usertype == common_def.USERTYPE_REGION_ADMIN:
            region = profile.region_id
            data['region'] = region if region else 0
        elif usertype == common_def.USERTYPE_SCHOOL_ADMIN:
            school = profile.school_id
            data['school'] = school if school else 0
        form = forms.adminForm1(request.user, profile, data, profile.region_id)
    ctx = RequestContext(request, {
        'form': form,
        'uid': uid,
        })
    return render_to_response('change_admin.html', ctx)

@has_permission('auth.change_sysadmin')
def misc_config(request):
    offline_timeout = None
    if request.POST.get('edit_offline_timeout'):
        form = forms.OfflineTimeoutForm(request.POST)
        if form.is_valid():
            s = form.cleaned_data['offline_timeout']
            r = models.MiscConfig.objects.get(pk='offline_timeout')
            r.conf_val = s
            r.save()
            log.log_change(request.user, r, u'修改离线时限')
    else:
        offline_timeout,_ = models.MiscConfig.objects.get_or_create(pk='offline_timeout')
        form = forms.OfflineTimeoutForm({
            'offline_timeout': offline_timeout.conf_val
            })
    ctx = RequestContext(request, {
        'form': form,
        })
    return render_to_response('misc_config.html', ctx)

@has_permission('change_semester')
@transaction.commit_on_success
def semester_list(request):
    level = 0
    if request.POST.has_key('add'):
        form = forms.SemesterForm(request.POST)
        level = int(request.POST['level'])+1
        if form.is_valid():
            semester = models.Semester.objects.create(
                name = form.cleaned_data['name'],
                start_date = form.cleaned_data['start_date'],
                end_date = form.cleaned_data['end_date'],
                region_id = request.session['region'],
                school_id = request.session.get('school'))
            log.log_addition(request.user, semester, u'添加学期')
            ctx = RequestContext(request, {
                'level': -level,
                })
            return render_to_response('history_goto.html', ctx)
    elif request.POST.has_key('delete'):
        ids = request.POST.getlist('selected')
        models.Semester.objects.filter(id__in=ids).delete()
        log.log_deletion(request.user, None, u'删除学期')
        form = forms.SemesterForm()
    else:
        form = forms.SemesterForm()
    semesters = db_util.get_semesters(request.session['region'], request.session.get('school'))
    ctx = RequestContext(request, {
        'form': form,
        'semesters': semesters,
        'level': level
        })
    return render_to_response('semester_list.html', ctx)

@login_required
def check_log(request):
    school = request.session.get('school')
    region = request.session.get('region')
    logs = LogEntry.objects.all()
    if school:
        logs = logs.filter(user__userprofile__school=school)
    elif region:
        logs = logs.filter(user__userprofile__region=region)
    if request.session['user_type'] == common_def.USERTYPE_TEACHER:
        logs = logs.filter(user=request.user)
    if request.GET.has_key('content'):
        content_type = request.GET['content']
        name = request.GET['name']
        logs = logs.filter(content_type__exact=content_type, object_repr__exact=name)
    elif request.GET.has_key('type'):
        logs = logs.filter(content_type__exact=request.GET['type'])
    elif request.GET.has_key('user'):
        logs = logs.filter(user=request.GET['user'])
    ctx = RequestContext(request, {
        'logs': logs
        })
    return render_to_response('log_page.html', ctx)
