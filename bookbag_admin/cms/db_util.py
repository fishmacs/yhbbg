#encoding=utf8

'''
Created on 2012-11-26

@author: zw
'''

import os
from datetime import date

from django.db.models import Q
from django.db import connections
from django.contrib.auth.models import Group

from bookbag.common import models, global_def as common_def, util as common_util

import global_def

def get_courseware_categories():
    if not global_def.courseware_categories:
        global_def.courseware_categories = models.CoursewareCategory.objects.all()     
    return [(c.id, c.name_ch) for c in global_def.courseware_categories]

def get_book_providers():
    if not global_def.book_providers:
        global_def.book_providers= models.BookProvider.objects.all()
    return [(p.id, p.name) for p in global_def.book_providers]

def delink_device(user):
    models.UserProfile.objects.filter(user=user).update(device_id='')
    for course in models.UserCourseware.objects.filter(user=user):
        try:
            if course.url:
                os.remove(course.url)#.encode('utf8'))
        except OSError:
            pass
        finally:
            course.delete()

def search_course(search, search_type):
    courses = models.Course.objects.all()
    if search:
        if search_type == 'name':
            courses = courses.filter(course_name__icontains=search)
                #course_start_date__isnull=False)
        elif search_type== 'ename':
            courses = courses.filter(english_name__icontains=search)
        else: #search_type == 'id'
            courses = courses.filter(cid__icontains=search)
                #course_start_date__isnull=False)
    return courses

def search_school(region, search=None, search_type=None, sortby='name'):
    schools = models.School.objects.filter(region=region, is_active=True)
    if search:
        if search_type == 'code':
            schools = schools.filter(code__icontains=search)
        else:
            schools = schools.filter(name__icontains=search)
    return schools.order_by(sortby)

def search_region(search, search_type):
    regions = models.Region.objects.filter(is_active=True)
    if search:
        if search_type == 'code':
            regions = regions.filter(code__icontains=search)
        else:
            regions = regions.filter(name__icontains=search)
    return regions.order_by('code')
    
def is_course_managable_by(grade, course_id, user):
    year = common_util.get_grade_year(grade)
    courses = models.TeacherClassCourse.objects.select_related('myclass').filter(course=course_id, teacher=user.id, myclass__is_active=True, myclass__year=year)
    return courses.count() > 0

def courses_of_teacher(user):
    courses = models.TeacherClassCourse.objects.select_related('myclass', 'course').filter(teacher=user, myclass__is_active=True).order_by('-myclass__year', 'course')
    ### distinct by fields not supported by sqlplus engine
    old = ()
    ret = []
    for c in courses:
        grade = c.myclass.get_grade()
        if (grade, c.course) != old:
            ret.append((grade, c.course))
            old = (grade, c.course)
    return ret

def get_all_classes(school_id, ignore_expired=True, return_tuple=False):
    classes = models.SchoolClass.objects.filter(school=school_id, is_active=True)
    if ignore_expired:
        classes = classes.filter(end_date__gt=date.today())
    if return_tuple:
        classes = tuple([(0, u'请选择班级')] + [(c.id, c.name) for c in classes])
    return classes

def classes_of_grade(school_id, grade):
    if grade:
        year = common_util.get_grade_year(grade)
        classes = models.SchoolClass.objects.filter(school=school_id, is_active=True, year=year)
    else:
        classes = []
    ret = [(c.id, c.name) for c in classes]
    return ret

def get_teacher_classes(user, grade, course):
    year = common_util.get_grade_year(grade)
    tcc_list = models.TeacherClassCourse.objects.select_related('myclass').filter(teacher=user, course=course, myclass__is_active=True, myclass__year=year)
    return [(x.myclass.id, x.myclass.name) for x in tcc_list]


def get_courseware_classes(courseware):
    cursor = connections['default'].cursor()
    cursor.execute('SELECT cc.schoolclass_id from courseware_classes cc INNER JOIN school_class sc ON cc.schoolclass_id=sc.id WHERE courseware_id=%d And sc.is_active>0' %courseware.id) 
    return [c[0] for c in cursor.fetchall()]

def create_class(name, grade, class_type, school, school_type):
    year = common_util.get_grade_year(grade)
    if school_type == common_def.SCHOOLTYPE_ELEMENTARY:
        start_year = year
        end_year = start_year+6
    elif school_type == common_def.SCHOOLTYPE_JUNIOR_HIGH:
        start_year = year+6
        end_year = start_year+3
    elif school_type == common_def.SCHOOLTYPE_SENIOR_HIGH:
        start_year = year+9
        end_year = start_year+3
    else: # HIGH
        start_year = year+6
        end_year = start_year+6
    start_date = date(start_year, 9, 1)
    end_date = date(end_year, 9, 1)
    clas = models.SchoolClass.objects.create(
        name=name, year=year,
        start_date=start_date,
        end_date=end_date,
        class_type_id=class_type,
        school_id=school)
    return clas

def get_all_regions():
    return models.Region.objects.filter(is_active=True).order_by('name')


GROUPS = {
    common_def.USERTYPE_SYSTEM_ADMIN: 'sysadmin',
    common_def.USERTYPE_REGION_ADMIN: 'regionadmin',
    common_def.USERTYPE_SCHOOL_ADMIN: 'schooladmin',
    common_def.USERTYPE_TEACHER: 'teacher'
}
    
def group_of_usertype(usertype):
    try:
        return Group.objects.get(name=GROUPS[usertype])
    except:
        return None

def semester_of_now(region, school):
    semester = get_current_semester(region, school)
    if semester:
        d = semester.start_date
        return d.month > 6 and 1 or 2
    else:
        month = date.today().month
        return 2 if 1 < month < 9 else 1

def get_current_semester(region, school):
    today = date.today()
    if school:
        semesters = models.Semester.objects.filter(Q(school=school)|Q(school__isnull=True,region=region), grade__isnull=True, start_date__lte=today, end_date__gte=today)
    else:
        semesters = models.Semester.objects.filter(region=region, school__isnull=True, grade__isnull=True, start_date__lte=today, end_date__gte=today)
    return semesters and semesters[0] or None
        
def courses_of_grade(region, school, grade):
    if grade:
        semester = semester_of_now(region, school)
        qs = models.GradeCourse.objects.select_related().filter(
            Q(school__isnull=True) | Q(school=school),
            Q(grade__isnull=True) | Q(grade=grade),
            Q(semester__isnull=True) | Q(semester=semester)).order_by('course')
    else:
        qs = []
    return [(x.course.id, x.course.course_name) for x in qs]

def get_semesters(region, school):
    return models.Semester.objects.select_related().filter(Q(region=region) | Q(school=school))
