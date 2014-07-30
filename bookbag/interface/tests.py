# encoding=utf8

#import re
#import urllib
import json

from django.test import Client, TestCase
from django.contrib.auth.models import User

from common import models


class TestSession:
    def __init__(self, username, user_id, user_type, token):
        self.username = username
        self.user_id = user_id
        self.user_type = user_type
        self.token = token

    def set_more(self, dict1):
        self.school = dict1['school_id']
        if self.user_type == 'student':
            grade = dict1['grade_id']
            clas = dict1['class_id']
            self.courses = [(c['course_id'], c['course_name'], grade, clas) for c in dict1['courses']]
        elif self.user_type == 'teacher':
            self.courses = [(c['course_id'], c['course_name'], c['grade_id'], c['class_id']) for c in dict1['courses']]


class TestBase(object):
    pass
    # def setup(self):
    #     super(unittest.TestCase, self).__init__()
    #     self.username = ''
    #     self.password = ''
        
    # def test_login(self):
    #     c = Client()
    #     res = c.post('/interface/login/', {
    #         'username': self.username,
    #         'password': self.password,
    #         })
    #     res.status_code
    #     ret = json.loads(res.read())
    #     self.session = TestSession(self.username, ret['user_id'], ret['user_type'], ret['token'])

        
class StudentTestCase(TestCase, TestBase):
    def setUp(self):
        self.username = 'student1'
        self.password = 'student123'
        u = User.objects.create(username=self.username)
        u.set_password(self.password)
        u.save()
        u.userprofile.school_id = 1
        u.userprofile.region_id = 1
        u.userprofile.save()


class TeacherTestCase(TestCase, TestBase):
    def setUp(self):
        self.username = 'teacher1'
        self.password = 'teacher123'
        u = User.objects.create(username=self.username)
        u.set_password(self.password)
        u.save()
        u.userprofile.school_id = 1
        u.userprofile.region_id = 1
        u.userprofile.save()

    def test_upload_yu(self):
        models.Course.objects.create(cid='0001', course_name=u'语文', english_name='Chinese')
        models.BookProvider.objects.create(name=u'人民教育出版社')
        models.CoursewareCategory.objects.create(name_ch=u'复习资料')
        c = Client()
        params = {'course': u'语文',
                  'username': 'teacher1',
                  'path': u'/Users/zw/Downloads/15_491113_网关网联协议.ppt',
                  'lesson_count': 5,
                  'grade': 8,
                  'category': u'复习资料'}
        res = c.post('/interface/courseware/upload/', {'data': json.dumps(params, ensure_ascii=False)})
        print res.content

