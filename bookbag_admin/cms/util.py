#encoding=utf8

#import sys
import os
import re
import csv
from chardet.universaldetector import UniversalDetector

from django.conf import settings
from django.db import transaction, connection
from django.contrib.auth.models import User

from bookbag.common import models

def upload_dir(uid, course_id):
    dir = os.path.join(settings.COURSEWARE_UPLOAD_DIR, uid, course_id)
    if not os.path.exists(dir):
        os.makedirs(dir)
    return dir

def handle_upload(f, dir):
    fn_nospace = re.sub(r'\s+', '_', f.name)
    filename = os.path.join(dir, fn_nospace)
    #print >>sys.stderr, 'uploading...', filename
    ### utf8 for apache
    #des = open(filename.encode('utf8'), 'wb+')
    ### don't need encode now, set LANG/LC_ALL when start apache
    des = open(filename.encode('utf8'), 'wb+')
    try:
        for chunk in f.chunks():
            des.write(chunk)
    finally:
        des.close()
    return filename

def import_user(f):
    batch_user(f, import_row)

def batch_delete(f):
    batch_user(f, delete_row)
    
def batch_user(f, row_func):
    encoding = detect_encoding(f)
    f.seek(0)
    reader = csv.reader(f)
    errlist = []
    classes = {}
    i = 1
    with transaction.commit_on_success():
        for row in reader:
            row_func(i, row, encoding, classes)
            i += 1
    if errlist:
        raise Exception('\n'.join(errlist))

gender_table = {
    u'男': 'M',
    u'女': 'F',
    'm': 'M',
    'male': 'M',
    'f': 'F',
    'female': 'F',
    }

def encode(s, encoding):
    try:
        return s.decode(encoding)
    except UnicodeDecodeError:
        return '???'
    
def import_row(i, row, encoding, classes):
    clsname,uid,name,gender,p1,p2 = [encode(field, encoding) for field in row]
    if p1 != p2:
        raise Exception(u'第%d行：密码不匹配!' % i)
    gender = gender_table.get(gender.lower(), '')
    if not gender:
        raise Exception(u'第%d行：性别不正确: %s' % (i, gender))
    
    cls = classes.get(clsname)
    if not cls:
        try:
            cls = models.SchoolClass.objects.get(name=clsname)
            classes[clsname] = cls
        except models.SchoolClass.DoesNotExist, e:
            raise Exception(u'第%d行：班级名不正确!' % i)
    user = User.objects.create(username=uid, first_name=name)
    user.set_password(p1)
    user.save()

    profile = user.userprofile
    profile.stu_class = cls
    profile.gender = gender
    profile.save()

def delete_row(i, row, encoding, classes):
    clsname,uid,name,gender,p1,p2 = [encode(field, encoding) for field in row]
    try:
        gender = gender_table[gender.lower()]
    except KeyError:
        raise Exception(u'第%d行：性别不正确: %s' % (i, gender))

    users = User.objects.select_related().filter(username=uid, first_name=name, userprofile__gender=gender, userprofile__stu_class__name=clsname)
    if not users:
        raise Exception(u'第%d行：用户信息不匹配，请检查用户的班级，id，姓名和性别信息' % i)
    user = users[0]
    if not user.check_password(p1):
        raise Exception(u'第%d行：用户密码不正确，情检查' % i)

    user.delete()

    # cursor = connection.cursor()
    # try:

    #     # valid user
    #     cursor.execute('SELECT id FROM auth_user u INNER JOIN user_profile p ON u.id=p.user_id \
    #                     INNER JOIN stu_class c ON p.stu_class_id=c.id WHERE u.username=%s AND \
    #                     u.first_name=%s AND p.gender=%s AND c.name=%s' % (uid,name,gender,clsname))
        
    # finally:
    #     cursor.close()
        
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

def set_course_classes(course_id, classes):
    with transaction.commit_on_success():
        cursor = connection.cursor()
        try:
            # update table course_classes
            cursor.execute('DELETE FROM course_classes WHERE course_id=%s' % course_id)
            for c in classes:
                cursor.execute('INSERT INTO course_classes(course_id, stuclass_id) VALUES(%s,%d)' % (course_id, c))
            # update table course_users
            cursor.execute('SELECT user_id FROM userprofile WHERE stu_class_id in (%s)' % ','.join([str(id) for id in classes]))
            all_users = [t[0] for t in cursor.fetchall()]
            cursor.execute('SELECT user_id FROM course_users WHERE course_id=%s' % course_id)
            user_set = set([t[0] for t in cursor.fetchall()])
            for u in all_users:
                if u not in user_set:
                    cursor.execute('INSERT INTO course_users(course_id, user_id) VALUES(%s,%d)' % (course_id, u))
        finally:
            cursor.close()

def set_class_courses(class_id, courses):
    with transaction.commit_on_success():
        cursor = connection.cursor()
        try:
            # update table course_classes
            cursor.execute('DELETE FROM course_classes WHERE stuclass_id=%s' % class_id)
            for c in courses:
                cursor.execute('INSERT INTO course_classes(course_id, stuclass_id) VALUES(%d,%s)' % (c, class_id))
            # upate table course_users
            cursor.execute('SELECT user_id FROM userprofile WHERE stu_class_id=%s' % class_id)
            cls_users = [t[0] for t in cursor.fetchall()]
            cursor.execute('SELECT user_id,course_id FROM course_users WHERE user_id in (%s)' \
                            % ','.join([str(uid) for uid in cls_users]))
            user_selected = set(cursor.fetchall())
            import sys
            print >>sys.stderr, user_selected
            for u in cls_users:
                for c in courses:
                    print >>sys.stderr, u, c
                    if (u,c) not in user_selected:
                        cursor.execute('INSERT INTO course_users(course_id, user_id) VALUES(%d,%d)' % (c, u))
        finally:
            cursor.close()

        # ucs = {}
        # for (u,c) in cursor.fetchall():
        #     try:
        #         ucs[u].append(c)
        #     except KeyError:
        #         ucs[u] = [c]
        # for profile in stu_class.userprofile_set.get_query_set():
        #     uid = profile.user_id
        #                (SELECT user_id FROM userprofile WHERE stu_class_id=%s) \
        #                 order by user_id' % class_id) 
        # for u, cs in ucs.iteritems():
        #     diff = course_set.difference(set(cs))
        #     print >>sys.stderr, 'diff', diff
        #     for d in diff:
                
    
