#encoding=utf-8

from django.conf.urls.defaults import patterns, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

import portal.views as v
import ask.views as av
import interface.views as iv
import interface.courseware as cv
import interface.qa as qv
import portal.voteviews as vv
import sync.views as sc

urlpatterns = patterns(
    '',
    (r'^$', v.course_page),
    (r'^(en|zh-\w+)/(\w+)/([^/]+)/([^/]+)/$', v.start_page),
    (r'^data/all/$', v.all_data0),
    (r'^data/all/(\w+)/$', v.all_data),
    #(r'^data/all/(\w+)/([^/]+)/([^/]+)/$', v.all_data),
    (r'^data/others/(\d+)/(\d+)/$', v.other_data),
    (r'^dl/getfile', v.getfile),
    (r'^dl/image/course/(\d+)/$', v.get_course_image),
    (r'^dl/image/courseware/(\d+)/$', v.get_courseware_image),
    # client interface
    (r'^download_ok/(\d+)/$', v.download_ok),
    (r'^offlinetimeout/$', v.offline_timeout),
    # (r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    (r'^login/$', v.login_page),
    (r'^logout/$', v.logout_page),
    # change password
    #(r'^ajax/user/prof/edit_passwd', v.change_password),
    (r'^user/profile/password/$', v.change_password),
    # user information
    (r'^user/information/$', v.user_information),
    # contacts
    (r'^contacts/(\d+)/$', v.contacts),
    # course schedule
    (r'^course/schedule/$', v.course_schedule),
    # school code list
    (r'^school/code/(\w+)/$', v.school_code),
    (r'^school/code/', v.school_code),

    # vote
    (r'^vote/list/(\w+)/$', vv.vote_list),
    (r'^course/controller/list/', vv.get_course_controller),
    (r'^vote/detail/(\w+)/$', vv.vote_detail),

    (r'^bigdata/log/upload/$', vv.upload_log),

    # sync
    #(r'^sync/controller/list/$', sc.controllers),
    (r'^sync/get/$', sc.sync_get),
    (r'^sync/(\d+)/(\d+)/start/$', sc.sync_start),
    (r'^sync/(\w+)/end/$', sc.sync_end),
    
    # ask search
    (r'^api/v1/', av.api),
    # (r'^ask/search/(\d+)/(?:(\d+)/)?$', av.ask_search),
    # web interface
    (r'^interface/login/$', iv.login),
    (r'^interface/user/properties/(\w+)/(\d+)/$', iv.user_properties),
    # change password
    (r'^interface/user/password/(\w+)/(\d+)/$', iv.change_password),
    (r'^interface/course/list/(\w+)/(\d+)/$', iv.course_list),
    (r'^interface/courseware/list/(\w+)/(\d+)/$', iv.courseware_list),
    (r'^interface/courseware/shared/(\w+)/(\d+)/(\d+)/(\d+)/$',
     iv.shared_coursewares),
    # 收藏
    (r'^interface/favorite/put/(\w+)/(\d+)/(\w+)/(\d+)/$', iv.put_favorite),
    (r'^interface/favorite/get/(\w+)/(\d+)/(\w*)/(\d+)/$', iv.get_favorite),
    (r'^interface/favorite/remove/(\w+)/(\d+)/(\d+)/$', iv.remove_favorite),
    # contacts
    (r'^interface/contacts/(\w+)/(\d+)/(\d+)/$', iv.get_contacts),
    # class space
    (r'^interface/classspace/question/list/(\w+)/(\d+)/(\d+)/(\d+)/$',
     qv.class_question_list),
    (r'^interface/classspace/question/add/(\w+)/(\d+)/(\d+)/(\d+)/$',
     qv.class_question_add),
    (r'^interface/classspace/post/list/(\w+)/(\d+)/(\d+)/$', qv.post_list),
    (r'^interface/classspace/post/add/(\w+)/(\d+)/(\d+)/$', qv.class_post_add),
    (r'^interface/classspace/post/edit/(\w+)/(\d+)/(\d+)/$', qv.post_edit),
    (r'^interface/classspace/post/delete/(\w+)/(\d+)/(\d+)/$', qv.post_delete),
    #(r'^interface/classspace/search/(\w+)/(\d+)/(\d+)/(\d+)/$', qv.cp_search),
    # question and answer
    (r'^interface/myqa/question/list/(\w+)/(\d+)/(\d+)/$',
     qv.qa_question_list),
    (r'^interface/myqa/question/add/(\w+)/(\d+)/(\d+)/$', qv.qa_question_add),
    (r'^interface/myqa/post/list/(\w+)/(\d+)/(\d+)/$', qv.post_list),
    (r'^interface/myqa/post/add/(\w+)/(\d+)/(\d+)/$', qv.qa_post_add),
    (r'^interface/myqa/post/edit/(\w+)/(\d+)/(\d+)/$', qv.post_edit),
    (r'^interface/myqa/post/delete/(\w+)/(\d+)/(\d+)/$', qv.post_delete),
    #(r'^interface/myqa/search/(\w+)/(\d+)/(\d+)/$', qv.qa_search),
    # courseware
    (r'^interface/courseware/add/(\w+)/(\d+)/(\d+)/(\d+)/$',
     cv.courseware_add),
    (r'^interface/courseware/edit/(\w+)/(\d+)/(\d+)/$', cv.courseware_edit),
    (r'^interface/courseware/delete/(\w+)/(\d+)/(\d+)/$',
     cv.courseware_delete),
    (r'^interface/courseware/convert/(\w+)/(\d+)/(\d+)/$',
     cv.courseware_convert),
    (r'^interface/courseware/deliver/(\w+)/(\d+)/(\d+)/$',
     cv.courseware_deliver),
    (r'^interface/courseware/undeliver/(\w+)/(\d+)/(\d+)/$',
     cv.courseware_undeliver),
    (r'^interface/courseware/state/(\d+)/$', cv.courseware_state),
    (r'^ajax/courseware/upload/progress/(\w+)/$', cv.upload_progress),

    # download
    (r'^interface/courseware/download/(\w+)/(\d+)/$', cv.courseware_download),
    # internal request from doc convert server
    (r'^convert_finish/$', cv.convert_finish),

    # media
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),

    # upload interface for YuChengwu
    (r'^interface/courseware/upload/$', cv.upload_yu),

    (r'^testing/', include('testing.urls')),
)

urlpatterns += staticfiles_urlpatterns()

from portal import signals

signals.connect_login()
