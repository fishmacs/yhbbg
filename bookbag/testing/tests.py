#encoding=utf-8

import json
import itertools
from datetime import date

from django.test import TestCase, Client
from django.contrib.auth.models import User

import loader
import xlsloader
from models import Test
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
    return user
    

def prepare_student():
    user = User.objects.create(username='student1')
    user.set_password('student123')
    user.save()

    profile = user.userprofile
    profile.usertype = global_def.USERTYPE_STUDENT
    profile.region_id = 1
    profile.school_id = 1
    profile.myclass_id = 1
    profile.save()

    return user

    
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
        self.client = Client()
        
    # def _test_import_csv(self):
    #     with open('testing/test.csv') as f:
    #         csvloader.load(f)

    def _test_import_xls(self):
        xlsloader.load('testing/data/unit1_tests.xlsx', 1)
        
    def test_testing(self):
        self._test_import_xls()
        self.client.get('/zh-CN/abc/teacher1/teacher123/')
        res = self.client.get('/testing/get/1/')
        self.assertEqual(res.status_code, 200)
        # data = json.loads(res.content)
        # print json.dumps(data['data'], indent=4, ensure_ascii=True)

    def test_load(self):
        loader.load('testing/data/unit1.xlsx')
        self.assertEqual(models.Courseware.objects.count(), 2)
        self.assertEqual(Test.objects.count(), 143)


class UploadTest(TestCase):
    def setUp(self):
        prepare_base()
        self.student = prepare_student()
        #prepare_courseware()
        self.client = Client()
        loader.load('testing/data/test.xlsx')

    def upload_one(self, data):
        res = self.client.post('/testing/result/put/', {'result': json.dumps(data, ensure_ascii=False)})
        self.assertEqual(res.status_code, 200)
        res = json.loads(res.content)
        self.assertEqual(res['result'], 'ok')
        
    def upload_result(self, student):
        # correct answers
        res = self.client.get('/zh-CN/abc/%s/student123/?mac=1' % student.username)
        self.assertEqual(res.status_code, 200)
        
        self.upload_one({'id': 1, 'answer': ['science', 'scientist']})
        self.upload_one({'id': 2, 'answer': ['beat']})
        self.upload_one({'id': 3, 'answer': ['defeat']})
        self.upload_one({'id': 4, 'answer': [2]})
        self.upload_one({'id': 5, 'answer': [1, 2, 3]})
        self.upload_one({'id': 6, 'answer': [0]})
        self.upload_one({'id': 7, 'answer': []})
        # repeat upload, confirm no new record inserted
        self.upload_one({'id': 1, 'answer': ['scientific', 'science', 'scientist']})
        
    def upload_result1(self, student):
        # mistake answers
        res = self.client.get('/zh-CN/abc/%s/student123/?mac=1' % student.username)
        self.assertEqual(res.status_code, 200)
        
        self.upload_one({'id': 1, 'answer': ['scientifi', 'science', 'scientist']})
        self.upload_one({'id': 2, 'answer': ['beet']})
        self.upload_one({'id': 3, 'answer': ['defeet']})
        self.upload_one({'id': 4, 'answer': [1]})
        self.upload_one({'id': 5, 'answer': [1, 2, 4]})
        self.upload_one({'id': 6, 'answer': [1]})
        # skip last test
        #self.upload_one({'id': 7, 'answer': []})
        # repeat upload, confirm no new record inserted
        self.upload_one({'id': 1, 'answer': ['science', 'scientist']})
        
    def test_upload_list(self):
        # correct answers
        self.upload_result(self.student)
        res = self.client.get('/testing/result/list/1/personal/')
        self.assertEqual(res.status_code, 200)
        res = json.loads(res.content)
        data = res['data']
        result = data[0]['result']
        questions = itertools.chain(*[r['questions'] for r in result])
        scores = [q['score'] for q in questions]
        self.assertEqual(scores, [1, 1, 1, 1, 1, 1, -2])
        
        res = self.client.get('/testing/result/list/1/1/')
        self.assertEqual(res.status_code, 200)
        res = json.loads(res.content)
        self.assertEqual(data, res['data'])

    def test_upload_list1(self):
        # mistake answers
        self.upload_result1(self.student)
        res = self.client.get('/testing/result/list/1/personal/')
        self.assertEqual(res.status_code, 200)
        res = json.loads(res.content)
        data = res['data']
        print json.dumps(data, ensure_ascii=False)
        result = data[0]['result']
        questions = itertools.chain(*[r['questions'] for r in result])
        scores = [q['score'] for q in questions]
        self.assertEqual(scores, [0, 0, 0, 0, 0, 0, -1])
        
        res = self.client.get('/testing/result/list/1/1/')
        self.assertEqual(res.status_code, 200)
        res = json.loads(res.content)
        self.assertEqual(data, res['data'])
        