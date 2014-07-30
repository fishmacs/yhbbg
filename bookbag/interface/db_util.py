#encoding=utf8

'''
Created on 2012-11-26

@author: zw
'''

import json
import hashlib
from datetime import datetime, date, timedelta

from django.conf import settings
from django.db.models import F, Q
from django.db import connections

from common import models as common_models, util as common_util, global_def as common_def
from portal import models
import global_def

### courseware methods
def get_courseware_categories():
    if not global_def.courseware_categories:
        global_def.courseware_categories = common_models.CoursewareCategory.objects.all()     
    return [(c.id, c.name_ch) for c in global_def.courseware_categories]

def get_book_providers():
    if not global_def.book_providers:
        global_def.book_providers= common_models.BookProvider.objects.all()
    return [(p.id, p.name) for p in global_def.book_providers]

def is_course_managable_by(grade, course_id, user):
    year = common_util.get_grade_year(grade)
    courses = common_models.TeacherClassCourse.objects.select_related('myclass').filter(course=course_id, teacher=user.id, myclass__is_active=True, myclass__year=year)
    return courses.count() > 0

def get_teacher_classes(user, grade, course):
    year = common_util.get_grade_year(grade)
    tcc_list = common_models.TeacherClassCourse.objects.select_related('myclass').filter(teacher=user, course=course, myclass__is_active=True, myclass__year=year)
    return [(x.myclass.id, x.myclass.name) for x in tcc_list]

def get_courseware_classes(courseware):
    cursor = connections['default'].cursor()
    cursor.execute('SELECT cc.schoolclass_id from courseware_classes cc inner join school_class sc ON cc.schoolclass_id=sc.id WHERE courseware_id=%d And sc.is_active>0' %courseware.id) 
    return [c[0] for c in cursor.fetchall()]

### interface methods
def search_course(search, search_type):
    if search and search_type:
        if search_type == 'name':
            return common_models.Course.objects.filter(
                course_name__icontains=search)
                #course_start_date__isnull=False)
        elif search_type== 'ename':
            return common_models.Course.objects.filter(
                english_name__icontains=search)
        else: #search_type == 'id'
            return common_models.Course.objects.filter(
                cid__icontains=search)
                #course_start_date__isnull=False)
    else:
        return common_models.Course.objects.all()#filter(

def get_userprofile(user):
    ut = type(user)
    if ut in [int, unicode]:
        return common_models.UserProfile.objects.get(user__pk=user)
    elif ut is common_models.UserProfile:
        return user
    else:
        return user.userprofile#models.UserProfile.objects.select_related('myclass').get(user__pk=user.id)

def get_usertype(uid, session):
    if 'user_type' in session:
        return session['user_type']
    else:
        profile = common_models.UserProfile.objects.get(user=uid)
        return profile.usertype
    
def get_student_courses(session):
    grade = session['grade']
    school = session['school']
    class_type = session['class_type']
    semester = date.today().month > 8 and 2 or 1
    cs = common_models.GradeCourse.objects.select_related('course').filter(
      Q(school__isnull=True) | Q(school=school),
      Q(class_type__isnull=True) | Q(class_type=class_type),
      Q(grade__isnull=True) | Q(grade=grade),
      Q(semester__isnull=True) | Q(semester=semester)).order_by('course')
    return [c.course for c in cs]

def get_teacher_courselist(user):
    course_refs = common_models.TeacherClassCourse.objects.select_related('course', 'myclass').filter(teacher=user, myclass__is_active=True).order_by('-myclass__year', 'course')
    #===========================================================================
    # ret = []
    # for c in courses:
    #    ret.append((c.myclass.get_grade(), c.myclass, c.course))
    # sorted(ret, lambda x: x[0])
    # return [{str(x):common_def.get_grade_display(x), \
    #         str(y.id):y.name, str(z.id):z.name} for (x,y,z) in ret]
    #===========================================================================
    ret = []
    for cr in course_refs:
        grade = cr.myclass.get_grade()
        ret.append({'grade_id': grade, 'grade_name': common_def.get_grade_display(grade),
                    'class_id': cr.myclass.id, 'class_name': cr.myclass.name,
                    'course_id': cr.course.id, 'course_name': cr.course.course_name})
    return ret

def get_student_coursewares(user, session):
    profile = get_userprofile(user)
    grade = session['grade']
    #===========================================================================
    # grade = session['grade']
    # class_type = session['class_type']
    # tcc_list = models.TeacherClassCourse.objects.filter(myclass=profile.myclass_id)
    # tids = [x.teacher_id for x in tcc_list]
    # return models.Courseware.objects.select_related('course','book_provider','teacher','category').filter(Q(class_type__isnull=True)|Q(class_type=class_type), teacher__in=tids, grade=grade, state__gte=common_def.COURSEWARE_STATE_FINISHED).order_by('course')
    #===========================================================================
    return common_models.Courseware.objects.select_related('course','book_provider','teacher','category').filter(grade=grade, classes=profile.myclass_id, state__gte=common_def.COURSEWARE_STATE_FINISHED).order_by('course', '-modified_time')

def find_new_coursewares(coursewares, courseware_ids, user, course_dict=None):
    ## find new coursewares
    delta = timedelta(seconds=settings.COURSEWARE_NEW_DURATION)
    dt = datetime.now() - delta
    mywares = common_models.UserCourseware.objects.filter(raw__id__in=courseware_ids, user=user, download_time__gt=F('raw__modified_time'))
    myware_dict = {}
    for ware in mywares:
        myware_dict[ware.raw_id] = ware

    newware_count = 0
    for courseware in coursewares:#courseware_list:
        if courseware.id not in myware_dict:
            if courseware.modified_time > dt:
                if course_dict:
                    course = course_dict[courseware.course_id]
                    course.newwares[courseware.category_id] += 1
                newware_count += 1
                courseware.new = True
            else:
                courseware.new = False
            courseware.downloaded = False
        else:
            courseware.new = False
            courseware.downloaded = True
    common_models.UserProfile.objects.filter(user=user).update(newware_count=newware_count)


class RepeatSave(Exception):
    pass

def save_favorite_courseware(user, type, courseware_id):
    flst = models.FavoriteStuff.objects.filter(user=user, courseware_id=courseware_id)
    if flst:
        raise RepeatSave()
    models.FavoriteStuff.objects.create(user=user, courseware_id=courseware_id, type=type)

def save_favorie_stuff(user, type, detail):
    hash = hashlib.md5(detail.encode('utf-8')).hexdigest()
    flst = models.FavoriteStuff.objects.filter(user=user, detail_hash=hash)
    if flst:
        raise RepeatSave()
    models.FavoriteStuff.objects.create(user=user, type=type, detail=detail, detail_hash=hash)

def read_favorite_stuff(user, type):
    return models.FavoriteStuff.objects.filter(user=user, type=type).order_by('type')

def read_favorite_courseware(user, type, course_id):
    it = int(type)
    types = []
    for t in [1,2]:
        if it&t != 0:
            types.append(str(t))
    return models.FavoriteStuff.objects.select_related('courseware', 'courseware__course', 'courseware__teacher').filter(
        user=user, type__in=types, courseware__course=course_id).order_by('type')

def get_teachers(class_id, name=None):
    qs = common_models.TeacherClassCourse.objects.select_related('teacher', 'teacher__userprofile', 'course').filter(myclass=class_id)
    if name:
        qs = qs.filter(teacher__first_name__icontains=name)
    qs = qs.order_by('course')
    contacts = []
    teacher_courses = {}
    for x in qs:
        teacher_id = x.teacher_id
        course_names = teacher_courses.get(teacher_id, [])
        if not course_names:
            teacher_courses[teacher_id] = course_names
            contacts.append((x.teacher, x.teacher.userprofile.contact))
        course_names.append(x.course.course_name)
    ret = []
    for t,c in contacts:
        item = {'name': t.first_name, 'course': teacher_courses[t.id]}
        item.update(get_contact(c))
        ret.append(item)
    return ret

def get_students_parents(class_id, name=None):
    ret = []
    cursor = connections['default'].cursor()
    if name:
        cursor.execute("select u.first_name, p.contact, h.relation, h.name, h.contact from userprofile p inner join auth_user u on p.user_id=u.id left join parent h on p.user_id=h.child_id where p.myclass_id=%s and u.first_name like %s order by u.first_name", [class_id, '%'+name+'%'])
    else:
        cursor.execute('select u.first_name, p.contact, h.relation, h.name, h.contact from userprofile p inner join auth_user u on p.user_id=u.id left join parent h on p.user_id=h.child_id where p.myclass_id=%s order by u.first_name', [class_id])
    for n1, c1, r, n2, c2 in cursor.fetchall():
        c1 = get_contact(c1)
        if c2:
            c2 = get_contact(c2)
        else:
            c2 = {}
        item = {
            'student_name': n1,
            'student_email': c1.get('email', ''),
            'student_tel': c1.get('tel', ''),
            }
        if n2:
            item.update({
                'parent_name': n2,
                'parent_relation': r==0 and u'父亲' or u'母亲',
                'parent_email': c2.get('email', ''),
                'parent_tel': c2.get('tel', ''),
                'parent_address': c2.get('address', ''),
                })
        ret.append(item)
    return ret
    
def get_contact(contact):
    return contact and json.loads(contact) or {}

