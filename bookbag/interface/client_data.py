import json

from common import global_def as common_def

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
        'name': courseware.name,
        'name_en': '',
        'course_id': courseware.course.id,
        'course_name': courseware.course.course_name, #courseware.get_course_name(),
        'course_name_en': courseware.course.english_name,
        'image': courseware.get_image_url(),
        'description': courseware.description,
        'url': '%sbookid=%d&password=%s&type=pdf' %(courseware.get_download_url(), courseware.id, courseware.password),
        'password': courseware.password,
        'state': courseware.state,
        'new': courseware.new,
        'downloaded': courseware.downloaded,
        'teacher': courseware.teacher.first_name,
        'upload_time': courseware.modified_time.strftime('%Y-%m-%d %H:%M:%S')
        }

def json_from_courseware(coursewares):
    d = []
    for courseware in coursewares:
        d.append(slice_courseware(courseware))
    return json.dumps(d, ensure_ascii=False)
