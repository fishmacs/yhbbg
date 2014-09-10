#encoding=utf-8

import urllib

from django.test import Client, TestCase
from django.contrib.auth.models import User

from portal.tests import prepare_base, prepare_teacher, prepare_student


def get_ask_tags(grade, course=None, class_id=None):
    if course:
        tagnames = 'course__%s ' % course
    else:
        tagnames = ''
    tagnames += 'grade__%s ' % grade
    if class_id:
        tagnames += 'class__%s discuss' % class_id
    else:
        tagnames += 'question'
    return tagnames


class SimpleTest(TestCase):
    def setUp(self):
        prepare_base()
        prepare_teacher()
        prepare_student()
        self.client = Client()
        
    def login(self, username, password, device='abc'):
        r = self.client.get('/zh-Han/%s/%s/%s/?mac=1' % (device, username, password))
        self.assertEqual(r.status_code, 200)

    def test_question_list(self):
        self.login('student1', 'student123')
        u = User.objects.get(username='student1')
        p = u.userprofile
        class_id = p.myclass.id
        grade = p.myclass.get_grade()
        params = urllib.urlencode({
            'format': 'json',
            'tags': get_ask_tags(grade, '语文'),
            'limit': 0,
        })
        r = self.client.get('/api/v1/thread/?' + params)
        self.assertEquals(r.status_code, 200)
        
        params = urllib.urlencode({
            'format': 'json',
            'tags': get_ask_tags(grade, '语文', class_id),
            'limit': 0,
        })
        r = self.client.get('/api/v1/thread/?' + params)
        self.assertEquals(r.status_code, 200)
        print r.content
        