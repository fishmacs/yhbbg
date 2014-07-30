'''
Created on 2013-3-19

@author: zw
'''

import json
import urllib
import urllib2

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

def get_ask_tags(request, grade, class_id=None):
    course = request.GET.get('course', '')
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

def question_list(request, grade, class_id=None):
    tags = get_ask_tags(request, grade, class_id).encode('utf8')
    params = urllib.urlencode({
        'format': 'json',
        'tags': tags,
        'limit': 0,
    })
    s = urllib.urlopen('%s/thread/?%s' %(settings.ASK_API_URL, params))
    return HttpResponse(s)
    
def question_add(request, grade, class_id=None):
    tags = get_ask_tags(request, grade, class_id)
    params = {
        'format': 'json',
        'username': request.user.username,
        #'api_key': _get_api_key(request),
        }
    data = json.dumps({
        'post_type': 'question',
        'title': request.POST['title'],
        'text': request.POST['text'],
        'tagnames': tags,
        })
    req = urllib2.Request('%s/post/?%s' %(settings.ASK_API_URL, urllib.urlencode(params)),
                          data=data,
                          headers={'Content-type': 'application/json'})
    try:
        s = urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        return HttpResponse(status=e.getcode(), content=e.read())
    return HttpResponse(s)

def post_list(request, token, uid, thread):
    params = urllib.urlencode({
        'format': 'json',
        'thread': thread,
        # 'username': request.user.username,
        # 'api_key': _get_api_key(request),
        'limit': 0,
    })
    s = urllib.urlopen('%s/post/?%s' %(settings.ASK_API_URL, params))
    return HttpResponse(s)

def post_add(request, token, uid, post, post_type):
    params = {
        'format': 'json',
        'username': request.user.username,
        #'api_key': _get_api_key(request),
        }
    data = json.dumps({
        'post_type': post_type,
        'post_id': post,
        'text': request.POST['text'],
        })
    try:
        req = urllib2.Request('%s/post/?%s' %(settings.ASK_API_URL, urllib.urlencode(params)),
                          data=data,
                          headers={'Content-type': 'application/json'})
    except urllib2.HTTPError, e:
        return HttpResponse(status=e.getcode(), content=e.read())
    s = urllib2.urlopen(req)
    return HttpResponse(s.read())

def post_edit(request, token, uid, post):
    params = {
        'format': 'json',
        'username': request.user.username,
        #'api_key': _get_api_key(request),
        }
    data = json.dumps({
        'text': request.POST['text'],
        })
    try:
        req = urllib2.Request('%s/post/%s/?%s' %(settings.ASK_API_URL, post, urllib.urlencode(params)),
                          data=data,
                          headers={'Content-type': 'application/json'})
    except urllib2.HTTPError, e:
        return HttpResponse(status=e.getcode(), content=e.read())
    ## method is PUT, not POST!
    req.get_method = lambda: 'PUT'
    s = urllib2.urlopen(req)
    return HttpResponse(s.read())

def post_delete(request, token, uid, post):
    params = {
        'format': 'json',
        'username': request.user.username,
        #'api_key': _get_api_key(request),
        }
    req = urllib2.Request('%s/post/%s/?%s' %(settings.ASK_API_URL, post, urllib.urlencode(params)))
    ## method is DELETE!
    req.get_method = lambda: 'DELETE'
    s = urllib2.urlopen(req)
    return HttpResponse(s.read())
