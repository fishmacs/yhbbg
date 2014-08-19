#encoding=utf-8

import json
from datetime import date

from django.test import TestCase, Client
from django.contrib.auth.models import User

import xlsloader
from common import models, global_def


def prepare_base():
    region = models.Region.objects.create(name=u'上海', code='abcd')
    school = models.School.objects.create(
        name='育才小学', code='abcd', type=1, region=region, region_name=u'上海')
    models.SchoolClass.objects.create(
        name=u'一班', year=2013, start_date=date(2013, 9, 1),
        end_date=date(2019, 7, 1), school=school)
    models.Course.objects.create(cid='001', course_name=u'语文')
    models.Course.objects.create(cid='002', course_name=u'数学')
    models.Course.objects.create(cid='003', course_name=u'英语')


def prepare_teacher():
    user = User.objects.create(username='teacher1')
    user.set_password('teacher123')
    user.save()

    profile = user.userprofile
    profile.usertype = global_def.USERTYPE_TEACHER
    profile.region_id = 1
    profile.school_id = 1
    profile.save()

    models.TeacherClassCourse.objects.create(
        teacher=user, myclass_id=1, course_id=1
    )


def prepare_courseware():
    models.CoursewareCategory.objects.create(name_ch=u'课堂讲义')
    models.BookProvider(u'人教版')
    models.Courseware.objects.create(
        name='test1', book_provider_id=1, category_id=1,
        course_id=1, teacher_id=1, grade=1, week=1, state=0,
        share_level=0
    )


class SimpleTest(TestCase):
    def setUp(self):
        prepare_base()
        prepare_teacher()
        prepare_courseware()
        self._test_import_xls()
        self.client = Client()
        
    # def _test_import_csv(self):
    #     with open('testing/test.csv') as f:
    #         csvloader.load(f)

    def _test_import_xls(self):
        xlsloader.load('testing/test.xlsx', 1)
        
    def test_testing(self):
        self.client.get('/zh-CN/abc/teacher1/teacher123/')
        res = self.client.get('/testing/get/1/')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.content)
        print json.dumps(data['data'], indent=2, ensure_ascii=True)

        