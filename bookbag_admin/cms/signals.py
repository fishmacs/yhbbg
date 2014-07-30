'''
Created on 2012-11-22

@author: zw
'''

from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in

from bookbag.common import models, global_def as common_def
import global_def

def logged_in(sender, user, request, **kwargs):
    profile = models.UserProfile.objects.select_related('school').get(user=user)
    request.session['user_type'] = profile.usertype
    if profile.region:
        request.session['region'] = profile.region_id
    if profile.school:
        request.session['school'] = profile.school.id
        request.session['school_type'] = profile.school.type
    if profile.usertype == common_def.USERTYPE_TEACHER:
        connect_teacher()
        
def connect_login():
    user_logged_in.connect(logged_in)

def update_courseware_categories(sender, **kwargs):
    global_def.courseware_categories = ()

def update_book_providers(sender, **kwargs):
    global_def.book_providers = ()
    
def connect_teacher():
    post_save.connect(update_courseware_categories, sender=models.CoursewareCategory, dispatch_uid='courseware_cms.cms.signals')
    post_delete.connect(update_courseware_categories, sender=models.CoursewareCategory, dispatch_uid='courseware_cms.cms.signals')    
    post_save.connect(update_book_providers, sender=models.BookProvider, dispatch_uid='courseware_cms.cms.signals')
    post_delete.connect(update_book_providers, sender=models.BookProvider, dispatch_uid='courseware_cms.cms.signals')
