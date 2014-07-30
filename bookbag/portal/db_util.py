'''
Created on 2012-11-23

@author: zw
'''

import json
from datetime import date, datetime, timedelta

from django.db import connections
from django.db.models import Q, F
from django.conf import settings

from common import models, global_def as common_def

def need_check_device(user):
    return len(models.UserAnyDevice.objects.filter(user=user)) == 0

def get_category_name(cat):
    category = models.CoursewareCategory.objects.get(pk=cat)
    return category.name_ch

def get_category_names(cat):
    category = models.CoursewareCategory.objects.get(pk=cat)     
    return category.name_ch, category.name_en

def get_userprofile(user):
    ut = type(user)
    if ut in [int, unicode]:
        return models.UserProfile.objects.get(user__pk=user)
    elif ut is models.UserProfile:
        return user
    else:
        return user.userprofile#models.UserProfile.objects.select_related('myclass').get(user__pk=user.id)

# def courses_of_user(user, session):
#     user_type = session['user_type']
#     if user_type == common_def.USERTYPE_STUDENT:
#         return get_student_courses(session)
#     elif user_type == common_def.USERTYPE_TEACHER:
#         return get_teacher_courses(user)
#     return []

def semester_of_now(session):
    semester = get_current_semester(session)
    if semester:
        d = semester.start_date
        return d.month > 6 and 1 or 2
    else:
        month = date.today().month
        return 2 if 1 < month < 9 else 1
    
def get_student_courses(session):
    grade = session['grade']
    school = session['school']
    class_type = session['class_type']
    semester = semester_of_now(session)
    cs = models.GradeCourse.objects.select_related('course').filter(
      Q(school__isnull=True) | Q(school=school),
      Q(class_type__isnull=True) | Q(class_type=class_type),
      Q(grade__isnull=True) | Q(grade=grade),
      Q(semester__isnull=True) | Q(semester=semester)).order_by('course')
    ret = []
    for c in cs:
        c1 = c.course
        c1.name = c1.course_name
        ret.append(c1)
    return ret


def get_teacher_courses(user, clss):
    course_refs = models.TeacherClassCourse.objects.select_related('course', 'myclass').filter(teacher=user, myclass__is_active=True).order_by('-myclass__year', 'course')
    if clss > 0:
        course_refs = course_refs.filter(myclass=clss)
    old = ()
    ret = []
    just_first_class = clss and clss < 0
    for c in course_refs:
        grade = c.myclass.get_grade()
        if clss < 0:
            clss = c.myclass.id
        if just_first_class and int(clss) != c.myclass.id:
            break
        if (grade, c.course.id) != old:
            ret.append(c.course)
            c.course.name = common_def.get_grade_display(grade) + c.course.course_name
            old = (grade, c.course.id)
    return ret, clss


# used by get_course_list1/voteview.get_course_controller
def get_teacher_courses1(user):
    courses = models.TeacherClassCourse.objects.select_related('course', 'myclass').filter(teacher=user, myclass__is_active=True).order_by('-myclass__year', 'course')
    return [(x.myclass_id, x.course) for x in courses]


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
    return models.Courseware.objects.select_related('course','book_provider','teacher','category').filter(grade=grade, classes=profile.myclass_id, state__gte=common_def.COURSEWARE_STATE_CONVERTED).order_by('course', '-modified_time')


def get_teacher_coursewares(user, clss):
    coursewares = models.Courseware.objects.select_related('course', 'book_provider', 'teacher', 'category').filter(teacher=user, state__gte=common_def.COURSEWARE_STATE_CONVERTED)
    if clss:
        coursewares = coursewares.filter(classes=clss)
    return coursewares.order_by('course', '-modified_time')


def get_course_list(user, session):
    user_type = session['user_type']
    if user_type == common_def.USERTYPE_STUDENT:
        return get_student_courses(session)
    elif user_type == common_def.USERTYPE_TEACHER:
        course_list, _ = get_teacher_courses(user.id, None)
        return course_list
    else:
        return []


# used by voteviews.get_course_controller
def get_course_list1(user, session):
    user_type = session['user_type']
    if user_type == common_def.USERTYPE_STUDENT:
        class_id = session.get('class_id', 6)
        courses = get_student_courses(session)
        return [(class_id, course) for course in courses]
    elif user_type == common_def.USERTYPE_TEACHER:
        return get_teacher_courses1(user.id)
    else:
        return []


def course_courseware_list(user, session, week=None, clss=None):
    user_type = session['user_type']
    if user_type == common_def.USERTYPE_STUDENT:
        course_list = get_student_courses(session)
        cs = get_student_coursewares(user, session)
    elif user_type == common_def.USERTYPE_TEACHER:
        course_list, myclass = get_teacher_courses(user.id, clss)
        cs = get_teacher_coursewares(user, myclass)
    else:
        return []

    if week:
        cs = cs.filter(week=week)

    course_dict = {}
    for c in course_list:
        course_dict[c.id] = c
        c.coursewares = {}
        c.newwares = {}

    courseware_ids = []
    #courseware_list = []
    for courseware in cs:
        #courseware_list.append(courseware)
        courseware_ids.append(courseware.id)
        category = courseware.category_id
        course = course_dict[courseware.course_id]
        if category not in course.coursewares:
            course.coursewares[category] = [courseware]
            course.newwares[category] = 0
        else:
            course.coursewares[category].append(courseware)
    find_new_coursewares(cs, courseware_ids, user, course_dict=course_dict)
    return course_list, cs  # courseware_list


def find_new_coursewares(coursewares, courseware_ids, user, course_dict=None):
    ## find new coursewares
    dt = datetime.now() - timedelta(seconds=settings.COURSEWARE_NEW_DURATION)
    mywares = models.UserCourseware.objects.filter(raw__id__in=courseware_ids, user=user, download_time__gt=F('raw__modified_time'))
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
    models.UserProfile.objects.filter(user=user).update(newware_count=newware_count)

def is_new_courseware(courseware_id, user):
    delivered = models.UserCourseware.objects.select_related('raw').get(raw=courseware_id, user=user)
    courseware = delivered.raw
    if not delivered.download_time or delivered.download_time < courseware.modified_time:
        dt = datetime.now() - timedelta(seconds=settings.COURSEWARE_NEW_DURATION)
        return courseware.modified_time > dt, delivered
    return False, delivered
    
def get_current_semester(session):
    today = date.today()
    region = session['region']
    school = session['school']
    grade = session.get('grade')
    semesters = models.Semester.objects.filter(Q(school=school)|Q(school__isnull=True,region=region), start_date__lte=today, end_date__gte=today)
    if grade:
        for s in semesters:
            if s.grade == grade:
                return s
    return semesters and semesters[0] or None

def get_teacher_classes(user):
    ## django model does support distinct on fields on sqlite backend
    cursor = connections['default'].cursor()
    cursor.execute('select distinct c.id, c.year, c.start_date, c.name from teacher_class_course t inner join school_class c on t.myclass_id=c.id where t.teacher_id=%d and c.is_active>0 order by c.year desc' % user.id)
    return cursor.fetchall()

def get_course_schedule(user):
    profile = user.userprofile
    class_id = profile.myclass_id
    schedule = models.CourseSchedule.objects.filter(myclass_id=class_id).order_by('weekday')
    return [_parse_courses(d.courses) for d in schedule]
        
def _parse_courses(courses):
    cs = [int(c) for c in courses.split(',')]
    return [{'course_id': i, 'course_name': _name_of_course(i)} for i in cs]


_course_dict = {}

def _name_of_course(course_id):
    global _course_dict
    
    if not _course_dict:
        courses = models.Course.objects.all()
        _course_dict = dict([(c.id, c.course_name) for c in courses])
    try:
        return _course_dict[course_id]
    except KeyError:
        try:
            course = models.Course.objects.get(pk=course_id)
            _course_dict[course_id] = course.course_name
            return course.course_name
        except: pass
    return ''

def shared_coursewares(user, grade, course, week):
    coursewares = models.Courseware.objects.filter(
        share_level__gt=common_def.SHARE_LEVEL_PRIVATE,
        #grade=grade,
        course_id=course,
        state__gte=common_def.COURSEWARE_STATE_CONVERTED).exclude(
            teacher=user).order_by('course', '-modified_time')
    if week:
        coursewares = coursewares.filter(week=week)
    find_new_shared_coursewares(coursewares, user)
    return coursewares

def find_new_shared_coursewares(coursewares, user):
    ## find new coursewares
    delta = timedelta(seconds=settings.COURSEWARE_NEW_DURATION)
    dt = datetime.now() - delta
    courseware_ids = [c.id for c in coursewares]
    mywares = models.UserCourseware.objects.filter(raw__id__in=courseware_ids, user=user, download_time__gt=F('raw__modified_time'))
    myware_dict = {}
    for ware in mywares:
        myware_dict[ware.raw_id] = ware

    for courseware in coursewares:#courseware_list:
        if courseware.id not in myware_dict:
            if courseware.modified_time > dt:
                courseware.new = True
            else:
                courseware.new = False
            courseware.downloaded = False
        else:
            courseware.new = False
            courseware.downloaded = True

def get_user_contacts(user, class_id):
    profile = models.UserProfile.objects.select_related('myclass', 'school').get(user=user)
    myschool = profile.school
    contacts = {}
    if myschool:
        contacts['school'] = {
            'name': myschool.name,
            'address': myschool.address,
            'tel': myschool.telphone,
            'email': myschool.email,
            'contacts': find_school_contacts(myschool.id),
        }
    myclass = profile.myclass
    if not myclass and class_id > 0:
        myclass = models.SchoolClass.objects.get(pk=class_id)

    if myclass:
        contacts['class'] = { 'name': myclass.get_name() }
        contacts['teachers'] = find_class_contacts(myclass.id)
        students, parents = get_student_contacts(myclass)
        contacts['students'] = students
        contacts['parents'] = parents
    return contacts
        
def get_student_contacts(myclass):
    students = []
    parents = []
    cursor = connections['default'].cursor()
    cursor.execute('select p.contact, u.first_name, h.contact, h.name from userprofile p inner join auth_user u on p.user_id=u.id left join parent h on p.user_id=h.child_id where p.myclass_id=%s order by u.first_name', [myclass.id])
    for c1, n1, c2, n2 in cursor.fetchall():
        students.append(get_contact(n1, c1))
        pc = get_contact(n2, c2)
        if pc:
            parents.append(pc)
    return students, parents
    
# def get_teacher_contacts(user):
#     classes = []
#     for cid,year,date,name in get_teacher_classes(user):
#         grade = util.calc_grade(year, date)
#         ucs = []
#         for p in models.UserProfile.objects.select_related('user').filter(myclass_id=cid).order_by('user__first_name'):
#             ucs.append(get_contact(p.user.first_name, p.contact))
#         classes.append({
#             'name': common_def.get_grade_display(grade)+name,
#             'contacts': find_class_contacts(cid),
#             'students': ucs,
#             })
#     return classes

def find_school_contacts(school_id):
    cursor = connections['default'].cursor()
    cursor.execute('select s.person_name, u.first_name, s.contact, p.contact from school_contacts s left join auth_user u on s.person_id=u.id left join userprofile p on s.person_id=p.user_id where s.school_id=%s', [school_id])
    ret = []
    for name1, name2, contact1,contact2 in cursor.fetchall():
        name = name1 or name2
        contact = contact1 or contact2
        if contact:
            ret.append(get_contact(name, contact))
    return ret

def find_class_contacts(class_id):
    cursor = connections['default'].cursor()
    cursor.execute('select c.person_name, u.first_name, c.contact, p.contact from class_contacts c left join auth_user u on c.person_id=u.id left join userprofile p on c.person_id=p.user_id where c.myclass_id=%s', [class_id])
    ret = []
    for name1, name2, contact1, contact2 in cursor.fetchall():
        name = name1 or name2
        contact = contact1 or contact2
        if contact:
            ret.append(get_contact(name, contact))
    return ret
    
def get_contact(name, contact):
    if not contact:
        return {}
    d = json.loads(contact)
    return {
        'name': name,
        'address': d.get('address', ''),
        'email': d.get('email', ''),
        'tel': d.get('tel', '')
        }
