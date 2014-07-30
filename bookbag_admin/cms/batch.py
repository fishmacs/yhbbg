#encoding=utf8

import os
import re
import csv
import json
from datetime import date
from chardet.universaldetector import UniversalDetector

from django.db import transaction, IntegrityError
from django.contrib.auth.models import User

import db_util
from bookbag.common import models, global_def as common_g

def detect_encoding(f):
    d = UniversalDetector()
    line = f.readline()
    while(line):
        d.feed(line)
        if d.done:
            break
        line = f.readline()
    result = d.close()
    if result['confidence'] < 0.95:
        return 'gb18030'
    enc = result['encoding']
    return enc=='gb2312' and 'gb18030' or enc

def batch_user(f, row_func):
    encoding = 'gb18030' #detect_encoding(f)
    f.seek(0)
    reader = csv.reader(f, delimiter=';')
    i = 1
    classes = {}
    with transaction.commit_on_success():
        for row in reader:
            try:
                row_func(row, encoding, classes)
            except Exception, e:
                raise Exception('第 %d 行: %s' %(i, str(e)))
            i += 1

def encode(s, encoding):
    try:
        return s.decode(encoding)
    except UnicodeDecodeError:
        return '???'
        
def add_teacher(row, encoding, classes):
    _,uid,passwd,_,_,_ = [encode(field, encoding) for field in row]
    teacher = User.objects.create(username=uid, first_name=uid, email='test@palmtao.com')
    teacher.set_password(passwd)
    teacher.groups.add(db_util.group_of_usertype(common_g.USERTYPE_TEACHER))
    teacher.save()
    profile = teacher.userprofile
    profile.usertype = common_g.USERTYPE_TEACHER
    profile.region_id = 1
    profile.school_id = 3
    profile.gender = 'M'
    profile.telphone = '18993159110'
    profile.contact = json.dumps({'tel': profile.telphone, 'email': teacher.email}, ensure_ascii=False)
    profile.save()
    for course_id in [1,2,3,7]:
        try:
            models.TeacherClassCourse.objects.create(teacher_id=teacher.id, myclass_id=13, course_id=course_id)
        except IntegrityError:
            pass

def add_student(row, encoding, classes):
    _,uid,passwd,_,_,_ = [encode(field, encoding) for field in row]
    student = User.objects.create(username=uid, first_name=uid, email='test@palmtao.com')
    student.set_password(passwd)
    student.save()
    profile = student.userprofile
    profile.usertype = common_g.USERTYPE_STUDENT
    profile.region_id = 1
    profile.school_id = 3
    profile.myclass_id = 13
    profile.gender = 'M'
    profile.birthday = date(2000, 3, 1)
    profile.telphone = '18993159110'
    profile.contact = json.dumps({'tel': profile.telphone, 'email': student.email}, ensure_ascii=False)
    profile.save()

def import_user(filename, usertype):
    with open(filename) as f:
        if usertype == 'teacher':
            batch_user(f, add_teacher)
        elif usertype == 'student':
            batch_user(f, add_student)

