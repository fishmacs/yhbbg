#encoding=utf8

import json
import urllib
import urllib2

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from wrapper import check_token
from ask import ask

@check_token
def class_question_list(request, token, uid, grade, class_id):
    # limit = request.GET.get('limit', '')
    # if limit:
    #     params['limit'] = limit
    return ask.question_list(request, grade, class_id)

@check_token
def qa_question_list(request, token, uid, grade):
    return ask.question_list(request, grade)

@check_token
@csrf_exempt
def class_question_add(request, token, uid, grade, class_id):
    return ask.question_add(request, grade, class_id)

@check_token
@csrf_exempt
def qa_question_add(request, token, uid, grade):
    return ask.question_add(request, grade)

@check_token
def post_list(request, token, uid, thread):
    return ask.post_list(request, token, uid, thread)

@check_token
@csrf_exempt
def class_post_add(request, token, uid, post):
    return ask.post_add(request, token, uid, post, 'comment')

@check_token
@csrf_exempt
def qa_post_add(request, token, uid, post):
    return ask.post_add(request, token, uid, post, 'answer')

@check_token
@csrf_exempt
def post_edit(request, token, uid, post):
    return ask.post_edit(request, token, uid, post)
    
@check_token
def post_delete(request, token, uid, post):
    return ask.post_delete(request, token ,uid, post)

# @check_token
# @csrf_exempt
# def cp_search(request, token, uid, grade, class_id):
#     return pask.ask_search(request, grade, class_id)

# @check_token
# @csrf_exempt
# def qa_search(request, token, uid, grade):
#     return pask.ask_search(request, grade)
