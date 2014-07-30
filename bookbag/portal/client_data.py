import json

from common import models, global_def as common_def
import db_util
import util


def slice_courseware(courseware):
    #catname, catname_en = db_util.get_category_names(courseware.category_id)
    return {
        'id': courseware.id,
        'provider_id': courseware.book_provider.id,
        'provider_name': courseware.book_provider.name,
        'provider_name_en': courseware.book_provider.name_en,
        'category_id': courseware.category.id,
        'category_name': courseware.category.name_ch,
        'category_name_en': courseware.category.name_en,
        'grade_id': courseware.grade,
        'grade_name': common_def.get_grade_display(courseware.grade),
        'volume_id': courseware.volume_id,
        'name': courseware.name,
        'name_en': '',
        'course_id': courseware.course.id,
        'course_name': courseware.course.course_name,  # courseware.get_course_name(),
        'course_name_en': courseware.course.english_name,
        'image': courseware.get_image_url(),
        'description': courseware.description,
        'url': courseware.get_absolute_url(),
        'password': courseware.password,
        'new': courseware.new,
        'downloaded': courseware.downloaded,
        'teacher': courseware.teacher.first_name,
        'upload_time': courseware.modified_time.strftime('%Y-%m-%d %H:%M:%S')
    }

    
def json_from_courseware(coursewares):
    d = {}
    for courseware in coursewares:
        d1 = d.get(courseware.course_id, {})
        if not d1:
            d[courseware.course_id] = d1
        l = d1.get(courseware.category_id, [])
        if not l:
            d1[courseware.category_id] = l
        l.append(slice_courseware(courseware))
    return json.dumps(d, ensure_ascii=False)

    
def json_from_courseware1(coursewares):
    d = []
    for courseware in coursewares:
        d.append(slice_courseware1(courseware))
    return json.dumps(d, ensure_ascii=False)

    
def slice_courseware1(courseware):
    #catname, catname_en = db_util.get_category_names(courseware.category_id)
    return {
        'id': courseware.id,
        'provider_id': courseware.book_provider.id,
        'provider_name': courseware.book_provider.name,
        'provider_name_en': courseware.book_provider.name_en,
        'category_id': courseware.category.id,
        'category_name': courseware.category.name_ch,
        'category_name_en': courseware.category.name_en,
        'grade_id': courseware.grade,
        'grade_name': common_def.get_grade_display(courseware.grade),
        'volume_id': courseware.volume_id,
        'name': courseware.name,
        'name_en': '',
        'image': '/dl/image/courseware/%d/' % courseware.id,
        'description': courseware.description,
        'url': courseware.get_download_url(),
        'password': courseware.password,
        'new': courseware.new,
        'downloaded': courseware.downloaded,
        'teacher': courseware.teacher.first_name,
        'upload_time': courseware.modified_time.strftime('%Y-%m-%d %H:%M:%S')
    }

    
def slice_course(course):
    return {
        'id': course.id,
        'course_name': course.course_name,
        'english_name': course.english_name,
        'image': '/dl/image/course/%d/' % course.id,
        'description': course.description,
    }

    
def json_from_course(courses):
    l_courses = []
    for course in courses:
        d_course = slice_course(course)
        l_courses.append(d_course)
        coursewares = {}
        newwares = {}
        for k, v in course.coursewares.iteritems():
            coursewares[k] = [slice_courseware1(cw) for cw in v]
        for k, v in course.newwares.iteritems():
            newwares[k] = v
        d_course['coursewares'] = coursewares
        d_course['newwares'] = newwares
    return json.dumps(l_courses, ensure_ascii=False)

    
def json_from_user(user):
    try:
        profile = models.UserProfile.objects.select_related('school', 'myclass').get(user=user)
        data = {
            'user_type': profile.get_usertype(),
            'school_id': profile.school and profile.school.id or 0,
            'school_name': profile.school and profile.school.name or '',
            'name': profile.user.first_name,
            'sex': profile.get_gender(),
            'age': profile.get_age(),
            'tel': profile.telphone,
            'address': profile.address
        }
        if profile.usertype == common_def.USERTYPE_STUDENT:
            data.update({
                'classes': [{
                    'grade_id': profile.myclass.get_grade(),
                    'grade_name': profile.myclass.get_grade_display(),
                    'class_id': profile.myclass.id,
                    'class_name': profile.myclass.name,
                }]})
        elif profile.usertype == common_def.USERTYPE_TEACHER:
            data.update({
                'classes': json_from_class(db_util.get_teacher_classes(user))
            })
    except models.UserProfile.DoesNotExist:
        data = {}
    return json.dumps(data, ensure_ascii=False)

    
def json_from_schedule(schedule):
    return json.dumps(schedule, ensure_ascii=False)

    
def json_from_class(classes):
    ret = []
    for cid, year, date, name in classes:
        grade = util.calc_grade(year, date)
        ret.append({'class_id': cid,
                    'class_name': name,
                    'grade_id': grade,
                    'grade_name': common_def.get_grade_display(grade)})
    return ret
    
