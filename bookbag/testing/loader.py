#encoding=utf-8

import os
import sys
import shutil
import re
import xlrd

from django.conf import settings
from django.contrib.auth.models import User
from django.db.transaction import commit_on_success

import xlsloader
from xlsloader import get_str, get_int
from common import course_ware
from common.models import SchoolClass, Course, Courseware, CoursewareCategory, BookProvider

sys.path.insert(1, os.path.abspath('..'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bookbag.settings")

teachers = {}
courses = {}
versions = {}
categories = {}


@commit_on_success
def load(filename):
    dir = os.path.dirname(filename)
    wb = xlrd.open_workbook(filename)
    sheet = wb.sheets()[0]
    i = 1
    for i in xrange(1, sheet.nrows):
        fields = sheet.row_values(i)
        types = sheet.row_types(i)
        name = get_str(fields[0], types[0])
        version = fields[1]
        category = fields[2]
        grade = get_int(fields[3], types[3])
        clss = fields[4]
        course = fields[5]
        user = get_str(fields[6], types[6])
        path = os.path.join(dir, fields[7])
        testfile = os.path.join(dir, fields[8])
        try:
            cwid = upload(name, version, category, grade, clss, course, user, path, testfile)
        except Exception:
            _, e, tb = sys.exc_info()
            e = Exception('第 %d 行：%s' % ((i + 1), e))
            raise e.__class__, e, tb
        else:
            xlsloader.load(testfile, cwid)


def get_model_id(model, dict, key, value, create=False):
    try:
        id = dict[value]
    except KeyError:
        try:
            o = model.objects.get(**{key: value})
        except model.DoesNotExist:
            if create:
                o = model.objects.create(**{key: value})
            else:
                print key, value
                raise Exception('指定的%s不存在!' % model)
        id = o.id
        dict[value] = id
    return id


def get_class_id(grade, name):
    qs = SchoolClass.objects.filter(name=name)
    for c in qs:
        if c.get_grade() == grade:
            return c.id
    raise Exception('指定的班级不存在！')

    
def upload(name, version, category, grade, clss, course, username, path, testfile):
    uid = get_model_id(User, teachers, 'username', username)
    version_id = get_model_id(BookProvider, versions, 'name', version, True)
    category_id = get_model_id(CoursewareCategory, categories, 'name_ch', category, True)
    class_id = get_class_id(grade, clss)
    course_id = get_model_id(Course, courses, 'course_name', course)

    filename = os.path.basename(path)
    desdir = os.path.join(settings.COURSEWARE_UPLOAD_DIR, str(uid), str(course_id))
    if not os.path.exists(desdir):
        os.makedirs(desdir)
    despath = os.path.join(desdir, re.sub(r'\s+', '_', filename))
    shutil.copy(path, despath)

    cw = Courseware.objects.create(
        name=name, grade=grade, week=1, volume_id='1', path=despath,
        course_id=course_id, teacher_id=uid, book_provider_id=version_id,
        category_id=category_id
    )
    cw.classes.add(class_id)
    if 'test' not in sys.argv:
        course_ware.convert_courseware(cw, False, '8001')
    return cw.id


if __name__ == '__main__':
    load(sys.argv[1])
    