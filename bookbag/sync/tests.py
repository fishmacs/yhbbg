#encoding=utf-8

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import json
from datetime import date

from django.test import TestCase, Client
from django.contrib.auth.models import User

from common import models as pm, global_def
#from models import LessonSync


def prepare_base():
    region = pm.Region.objects.create(name=u'上海', code='abcd')
    school = pm.School.objects.create(
        name='育才小学', code='abcd', type=1, region=region, region_name=u'上海')
    pm.SchoolClass.objects.create(
        name=u'一班', year=2013, start_date=date(2013, 9, 1),
        end_date=date(2019, 7, 1), school=school)
    pm.Course.objects.create(cid='001', course_name=u'语文')
    pm.Course.objects.create(cid='002', course_name=u'数学')
    pm.Course.objects.create(cid='003', course_name=u'英语')


def prepare_teacher():
    user = User.objects.create(username='teacher1')
    user.set_password('teacher123')
    user.save()

    profile = user.userprofile
    profile.usertype = global_def.USERTYPE_TEACHER
    profile.region_id = 1
    profile.school_id = 1
    profile.save()

    pm.TeacherClassCourse.objects.create(
        teacher=user, myclass_id=1, course_id=1)


def prepare_student():
    user = User.objects.create(username='student1')
    user.set_password('student123')
    user.save()

    profile = user.userprofile
    profile.region_id = 1
    profile.school_id = 1
    profile.myclass_id = 1
    profile.save()

    pm.GradeCourse.objects.create(course_id=1)
    pm.GradeCourse.objects.create(course_id=2)
    pm.GradeCourse.objects.create(course_id=3)


class SimpleTest(TestCase):
    def setUp(self):
        prepare_base()
        self.student = prepare_student()
        self.teacher = prepare_teacher()
        self.client = Client()
        
    def test_sync_get(self):
        self.client.get('/zh-CN/abc/teacher1/teacher123/')
        res = self.client.get('/sync/get/')
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d['data'], {})
        
    def test_sync_get2(self):
        self.client.get('/zh-CN/abc/student1/student123/')
        res = self.client.get('/sync/get/')
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d['data'], {})

    # def test_sync_start(self):
    #     print '--------sync_start------------'
    #     self.client.get('/zh-CN/abc/teacher1/teacher123/')
    #     res = self.client.get('/sync/1/1/start/')
    #     self.assertEqual(res.status_code, 200)
        
    def test_sync_start_end(self):
        print '--------sync_start/end------------'
        self.client.get('/zh-CN/abc/teacher1/teacher123/')
        res = self.client.get('/sync/1/1/start/')
        self.assertEqual(res.status_code, 200)
        # insert new ones, do not overwrite old one
        # # start again, make sure the old one is cleared
        # res = self.client.get('/sync/1/1/start/')
        # self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        d = d['data']
        res = self.client.get('/sync/{0}/end/'.format(d['sync_id']))
        self.assertEqual(res.status_code, 200)

    def test_sync_get3(self):
        self.client.get('/zh-CN/abc/teacher1/teacher123/')
        res = self.client.get('/sync/1/1/start/')
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        id = d['data']['sync_id']
        
        res = self.client.get('/sync/get/')
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d['data']['sync_id'], id)

        res = self.client.get('/zh-CN/xyz/student1/student123/')
        res = self.client.get('/sync/get/')
        self.assertEqual(res.status_code, 200)
        d = json.loads(res.content)
        self.assertEqual(d['data']['sync_id'], id)
        
        self.client.get('/zh-CN/abc/teacher1/teacher123/')
        res = self.client.get('/sync/{0}/end/'.format(id))
        self.assertEqual(res.status_code, 200)
        