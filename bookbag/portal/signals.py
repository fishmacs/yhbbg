'''
Created on 2012-11-22

@author: zw
'''

from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in

from common import models
import db_util
import util

# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         models.UserProfile.objects.create(user=instance)

# # multiple imports causes multiple registers and multiple creation of userprofile
# # resolve with displath_uid argument
# def connect_userprofile():
#     post_save.connect(create_user_profile, sender=User, dispatch_uid='courseware.portal.models')


def logged_in(sender, user, request, **kwargs):
    profile = models.UserProfile.objects.select_related('school', 'myclass').get(user__pk=user.id)
    request.session['user_type'] = profile.usertype
    if profile.school:
        request.session['school'] = profile.school.id
        request.session['school_type'] = profile.school.type
        request.session['region'] = profile.school.region_id
    if profile.myclass:
        request.session['grade'] = profile.myclass.get_grade()
        request.session['class_id'] = profile.myclass_id
        request.session['class_type'] = profile.myclass.class_type_id
    semester = db_util.get_current_semester(request.session)
    if semester:
        request.session['semester'] = semester.id
        request.session['semester_start'] = semester.start_date
    else:
        request.session['semester_start'] = util.guess_semester_start()

def connect_login():
    user_logged_in.connect(logged_in)
