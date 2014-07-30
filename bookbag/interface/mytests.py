# encoding=utf8

import re
import urllib
import json

TEST_SERVER = {
    'local': 'http://localhost:8080',
    'bookbag_demo': 'http://bookbag.palmtao.com',
    'bookbag': 'https://bookbag',
    'unicom': 'https://bookbag.unicomedu.com',
    }

class TestSession:
    def __init__(self, server, username, user_id, user_type, token):
        self.server = server
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

def get_test_server(name):
    return TEST_SERVER[name]

def test_login(servername, username, password):
    data = urllib.urlencode({
        'username': username,
        'password': password,
        })
    server = get_test_server(servername)
    res = urllib.urlopen('%s/interface/login/' % server, data)
    ret = json.loads(res.read())
    return TestSession(server, username, ret['user_id'], ret['user_type'], ret['token'])

def test_user_info(s):
    res = urllib.urlopen('%s/interface/user/properties/%s/%d/' %(s.server, s.token, s.user_id))
    dict1 = json.loads(res.read())
    res = urllib.urlopen('%s/interface/course/list/%s/%d/' %(s.server, s.token, s.user_id))
    courses = json.loads(res.read())
    dict1.update({'courses': courses})
    s.set_more(dict1)

def test_coursewares(ss):
    res = urllib.urlopen('%s/interface/courseware/list/%s/%d/' %(ss.server, ss.token, ss.user_id))
    return res.read()

def test_shared_coursewares(ss):
    s = set()
    for course_id, course_name, grade, _ in ss.courses:
        e = (course_id, grade)
        if e not in s:
            s.add(e)
            res = urllib.urlopen('%s/interface/courseware/shared/%s/%d/%d/%d/' %(ss.server, ss.token, ss.user_id, grade, course_id))
            print '--------- %d, %s, coursewares---------' % (grade, course_name.encode('utf8'))
            print res.read()
            print

def test_class_question_list(ss, i=0):
    _, course_name, grade, class_id = ss.courses[i]
    params = urllib.urlencode({
        'course': course_name.encode('utf8')
        })
    res = urllib.urlopen('%s/interface/classspace/question/list/%s/%d/%d/%d?%s' %(ss.server, ss.token, ss.user_id, grade, class_id, params))
    return res.read()
        
def test_class_question_add(ss, title, text, i=0):
    data = urllib.urlencode({
        'title': title,
        'text': text,
        })
    _, course_name, grade, clas = ss.courses[i]
    params = urllib.urlencode({
        'course': course_name.encode('utf8')
        })
    res = urllib.urlopen('%s/interface/classspace/question/add/%s/%d/%d/%d/?%s' %(ss.server, ss.token, ss.user_id, grade, clas, params), data)
    #return res.read()
    d = json.loads(res.read())
    post_id = int(d['id'])
    thread_id = int(re.sub('/(?:\w+/)+(\d+)/$', '\\1', d['thread']))
    return post_id, thread_id

def test_class_post_add(ss, post_id, text):
    data = urllib.urlencode({
        'text': text,
        })
    res = urllib.urlopen('%s/interface/classspace/post/add/%s/%d/%d/' %(ss.server, ss.token, ss.user_id, post_id), data)
    d = json.loads(res.read())
    post_id = int(d['id'])
    parent_id = int(re.sub('/(?:\w+/)+(\d+)/$', '\\1', d['parent']))
    thread_id = int(re.sub('/(?:\w+/)+(\d+)/$', '\\1', d['thread']))
    return post_id, parent_id, thread_id

def test_qa_question_list(ss, i=0):
    _, course_name, grade, _ = ss.courses[i]
    params = urllib.urlencode({
        'course': course_name.encode('utf8')
        })
    res = urllib.urlopen('%s/interface/myqa/question/list/%s/%d/%d/?%s' %(ss.server, ss.token, ss.user_id, grade, params))
    return res.read()

def test_qa_question_add(ss, title, text, i=0):
    data = urllib.urlencode({
        'title': title,
        'text': text,
        })
    _, course_name, grade, _ = ss.courses[i]
    params = urllib.urlencode({
        'course': course_name.encode('utf8')
        })
    res = urllib.urlopen('%s/interface/myqa/question/add/%s/%d/%d/?%s' %(ss.server, ss.token, ss.user_id, grade, params), data)
    #return res.read()
    d = json.loads(res.read())
    post_id = int(d['id'])
    thread_id = int(re.sub('/(?:\w+/)+(\d+)/$', '\\1', d['thread']))
    return post_id, thread_id

def test_qa_post_add(ss, post_id, text):
    data = urllib.urlencode({
        'text': text,
        })
    res = urllib.urlopen('%s/interface/myqa/post/add/%s/%d/%d/' %(ss.server, ss.token, ss.user_id, post_id), data)
    d = json.loads(res.read())
    post_id = int(d['id'])
    thread_id = int(re.sub('/(?:\w+/)+(\d+)/$', '\\1', d['thread']))
    return post_id, thread_id

### these 3 functions are same with classspace/myqa
def test_post_list(ss, thread_id):
    res = urllib.urlopen('%s/interface/myqa/post/list/%s/%d/%d/' %(ss.server, ss.token, ss.user_id, thread_id))
    return res.read()

def test_post_edit(ss, post_id, text):
    data = urllib.urlencode({
        'text': text,
        })
    res = urllib.urlopen('%s/interface/classspace/post/edit/%s/%d/%d/' %(ss.server, ss.token, ss.user_id, post_id), data)
    return res.read()
    # d = json.loads(res.read())
    # post_id = int(d['id'])

def test_post_delete(ss, post_id):
    res = urllib.urlopen('%s/interface/classspace/post/delete/%s/%d/%d/' %(ss.server, ss.token, ss.user_id, post_id))
    return res.read()
    
def write_error(str):
    f = open('/Users/zw/abc.html', 'w')
    f.write(str)
    f.close()

def test_qa_search(ss, search_type, search, i=0):
    data = urllib.urlencode({
        'search_type': search_type,
        'text': search
        })
    _, course_name, grade, _ = ss.courses[i]
    params = urllib.urlencode({
        'course': course_name.encode('utf8')
        })
    r = urllib.urlopen('%s/interface/myqa/search/%s/%d/%d/?%s' %(ss.server, ss.token, ss.user_id, grade, params), data)
    return r.read()

def test_class_search(ss, search_type, search, i=0):
    data = urllib.urlencode({
        'search_type': search_type,
        'text': search
        })
    _, course_name, grade, clss = ss.courses[i]
    params = urllib.urlencode({
        'course': course_name.encode('utf8')
        })
    r = urllib.urlopen('%s/interface/classspace/search/%s/%d/%d/%d/?%s' %(ss.server, ss.token, ss.user_id, grade, clss, params), data)
    return r.read()

def test_ask(srvname, username, password):
    print '-------------- test login: ---------------'
    ss = test_login(srvname, username, password)
    print '-------------- login ok! ---------------\n'

    print '-------------- test user info: ---------------'
    test_user_info(ss)
    print '-------------- user info ok! ---------------\n'

    print '-------------- test myqa: ---------------'
    print '...... adding question ......'
    post, thread = test_qa_question_add(ss, '测试我的问答主题功能 add add add:', '主题内容内容我主题内容内容主题内容内容主题内容内容')
    print post, thread
    print '...... adding post ......'
    ppost = post
    post, thread = test_qa_post_add(ss, post, '我来回复 我来回复 我来回复 我来回复！')
    print post, thread

    print '...... editting post ......'
    test_post_edit(ss, post, '我来修改 我来修改 我来修改 我来修改！')

    print '...... listing questions ......'
    print test_qa_question_list(ss)

    print '...... listing posts of thread %d......' % thread
    print test_post_list(ss, thread)

    print '...... deleting posts %d, %d' % (post, ppost)
    test_post_delete(ss, post)
    test_post_delete(ss, ppost)

    print '-------------- myqa ok! ---------------'

    print '-------------- test classspace: ---------------'
    print '...... adding question ......'
    post, thread = test_class_question_add(ss, '测试班级空间主题功能 add add add:', '主题内容内容我主题内容内容主题内容内容主题内容内容')
    print post, thread
    print '...... adding post ......'
    post, ppost, thread = test_class_post_add(ss, post, '我来回复 我来回复 我来回复 我来回复！')
    print post, ppost, thread

    print '...... editting post ......'
    test_post_edit(ss, post, '我来修改 我来修改 我来修改 我来修改！')

    print '...... listing questions ......'
    print test_class_question_list(ss)

    print '...... listing posts of thread %d......' % thread
    print test_post_list(ss, thread)

    print '...... deleting posts %d, %d' % (post, ppost)
    test_post_delete(ss, post)
    test_post_delete(ss, ppost)

    print '-------------- classspace ok! ---------------'
    

def test_put_favorite(ss, type, cid, detail=None):
    if detail:
        data = urllib.urlencode({
            'detail': detail,
        })
        res = urllib.urlopen('%s/interface/favorite/put/%s/%d/%s/%d/' %(ss.server, ss.token, ss.user_id, type, cid), data)
    else:
        res = urllib.urlopen('%s/interface/favorite/put/%s/%d/%s/%d/' %(ss.server, ss.token, ss.user_id, type, cid))
    return res.read()

def test_get_favorite(ss, type):
    for course_id,_,_,_ in ss.courses:
        res = urllib.urlopen('%s/interface/favorite/get/%s/%d/%s/%d/' %(ss.server, ss.token, ss.user_id, type, course_id))
        print res.read()

def test_remove_favorite(ss, fid):
    res = urllib.urlopen('%s/interface/favorite/remove/%s/%d/%d/' %(ss.server, ss.token, ss.user_id, fid))
    return res.read()

def test_contacts(ss):
    for _,_,_,class_id in ss.courses:
        res = urllib.urlopen('%s/interface/contacts/%s/%d/%d/' %(ss.server, ss.token, ss.user_id, class_id))
        print res.read()

def test_upload_yu():
    params = {'course': u'语文',
              'username': 'teacher1',
              'path': u'/Users/zw/Downloads/15_491113_网关网联协议.ppt',
              'lesson_count': 5,
              'grade': 8,
              'category': u'复习资料'}
    params = {'data': json.dumps(params)}
    res = urllib.urlopen('http://localhost:8000/interface/courseware/upload/', urllib.urlencode(params))
    print res.read()

    
if __name__ == '__main__':
    import sys
    test_ask(sys.argv[1], sys.argv[2], sys.argv[3])
