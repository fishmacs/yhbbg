#encoding=utf8

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

import random
import json
from datetime import datetime, date
from collections import namedtuple
from stompest.sync import Stomp
from stompest.config import StompConfig

from django.test import TestCase, Client
from django.test.simple import DjangoTestSuiteRunner
from django.contrib.auth.models import User

from common import models, global_def
from common.mongo_models import Vote, EmbeddedUser, EmbeddedOwner, Option


def dict2namedtuple(name, dict):
    NamedTuple = namedtuple(name, ' '.join(dict.keys()))
    return NamedTuple(**dict)


def get_stomp(mq):
    config = StompConfig(mq.url, login=mq.username, passcode=mq.password)
    stomp = Stomp(config)
    stomp.connect(host=mq.broker)
    return stomp


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

    models.GradeCourse.objects.create(course_id=1)
    models.GradeCourse.objects.create(course_id=2)
    models.GradeCourse.objects.create(course_id=3)


class MyTestRunner(DjangoTestSuiteRunner):
    mongodb_name = 'testsuite'

    def setup_databases(self, **kwargs):
        from mongoengine.connection import connect, disconnect
        disconnect()
        connect(self.mongodb_name)
        print 'Creating mongo test-database ' + self.mongodb_name
        return super(MyTestRunner, self).setup_databases(**kwargs)

    def teardown_databases(self, old_config, **kwargs):
        from mongoengine.connection import get_connection, disconnect
        connection = get_connection()
        connection.drop_database(self.mongodb_name)
        print 'Dropping mongo test-database: ' + self.mongodb_name
        disconnect()
        super(MyTestRunner, self).teardown_databases(old_config, **kwargs)


class MyTest(TestCase):
    def setUp(self):
        prepare_base()
        prepare_student()
        prepare_teacher()
        self.student = User.objects.get(username='student1')
        self.teacher = User.objects.get(username='teacher1')
        self.stu_client = Client()
        self.stu_client.post('/login/', {
            'username': 'student1',
            'password': 'student123'
        })
        self.t_client = Client()
        self.t_client.post('/login/', {
            'username': 'teacher1',
            'password': 'teacher123'
        })

    def tearDown(self):
        self.stu_client.get('/logout/')
        self.t_client.get('/logout/')

    def prepare_vote(self):
        from mongoengine import connection
        connection.connect(MyTestRunner.mongodb_name)
        Vote.objects.create(
            title='test',
            kind='multiple',
            min_choice=1,
            max_choice=4,
            start_time=datetime.now(),
            started=True,
            owner=EmbeddedOwner(id='1_1', name=u'语文'),
            creator=EmbeddedUser(id=str(self.teacher.id),
                                 name=self.teacher.username),
            options=[Option(content=str(i+1)) for i in xrange(4)]
        )

    def test_vote(self):
        self.prepare_vote()
        self.vote = None
        self._test_controller()
        self._test_vote_list()
        self._test_vote_vote()

    def _test_controller(self):
        print '======== test controller start ========'
        res = self.stu_client.get('/course/controller/list/')
        print json.loads(res.content)
        res = self.t_client.get('/course/controller/list/')
        print json.loads(res.content)
        print '======== test controller end ========'

    def _test_vote_list(self):
        print '======== test vote list start ========'
        res = self.stu_client.get('/vote/list/1_1/')
        votes = json.loads(res.content)
        if votes:
            vote = votes[random.randint(0, len(votes)-1)]
            self.vote = dict2namedtuple('vote', vote)
        res = self.t_client.get('/vote/list/1_1/')
        votes = json.loads(res.content)
        print '======== test vote list end ========'

    def _test_vote_vote(self):
        print '======== test vote start ========'
        if self.vote:
            choices = range(len(self.vote.options))
            n = random.randint(self.vote.min_choice, self.vote.max_choice)
            i = random.randint(0, len(choices) - 1)
            choices *= 2
            selections = sorted([choices[x] for x in xrange(i, i+n)])
            data = {
                'vote_id': self.vote.vote_id,
                'user_id': self.student.id,
                'user_name': self.student.username,
                'selections': selections
            }
            print 'voting %s...' % self.vote.vote_id
            print 'destination is %s' % self.vote.destination
            stomp = get_stomp(dict2namedtuple('mq', self.vote.message_queue))
            stomp.send(self.vote.destination, json.dumps(data))
            print 'voted'
        else:
            print 'no active vote...'
        print '======== test vote end ========'
