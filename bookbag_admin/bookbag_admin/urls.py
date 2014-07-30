from django.conf.urls import patterns
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.conf import settings

from cms import views as view
from cms import courseware as cv
from cms import voteviews as vv

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^$', view.main_page),
    (r'^courses/$', view.course_page),

    # session
    (r'^login/$', 'django.contrib.auth.views.login',
     {'template_name': 'login.html'}),
    (r'^logout/$', view.logout_page),

    # admin
    (r'^check_log/$', view.check_log),
    (r'^misc_config/$', view.misc_config),

    # region management
    (r'^region/list/$', view.region_list),
    (r'^region/add/$', view.region_add),
    (r'^region/edit/(\d+)/$', view.region_edit),

    # school management
    (r'^school/list/(\d+)/$', view.school_list),
    (r'^school/add/(\d+)/$', view.school_add),
    (r'^school/edit/(\d+)/$', view.school_edit),

    # semester management
    (r'^semester/list/$', view.semester_list),

    # class management
    (r'^class/list/(\d+)/$', view.class_list),
    (r'^class/add/(\d+)/$', view.class_add),
    (r'^class/edit/(\d+)/$', view.class_edit),

    # student management
    (r'^student/list/$', view.student_list),
    (r'^student/add/$', view.student_add),
    (r'^student/edit/$', view.student_edit),

    # admin management
    (r'^admin/list/$', view.admin_list),
    (r'^admin/add/$', view.admin_add),
    (r'^admin/edit/$', view.admin_edit),

    # teacher management
    (r'^teacher/list/$', view.teacher_list),
    (r'^teacher/add/$', view.teacher_add),
    (r'^teacher/edit/$', view.teacher_edit),
    (r'^teacher/class_course/(\d+)/$', view.teacher_class_course),

    # batch import/delete
    (r'^import/(\w+)/$', view.import_user),
    (r'^batch_del/(\w+)/$', view.batch_del_user),

    # course management
    (r'^course/add/$', view.add_course),
    (r'^course/edit/$', view.edit_course),
    (r'^course/list/$', view.course_list),

    # courseware management
    (r'^coursewares/(\d+)/(\d+)/$', cv.coursewares),
    (r'^courseware/detail/(\d+)/$', cv.courseware_detail),
    (r'^courseware/convert/(\d+)/$', cv.courseware_convert),
    (r'^courseware/deliver/(\d+)/$', cv.courseware_deliver),
    (r'^courseware/undeliver/(\d+)/$', cv.courseware_undeliver),

    # internal request from doc convert server
    (r'^convert_finish/$', cv.convert_finish),
    #(r'^deliver_finish/$', view.deliver_finish),

    # vote
    (r'^vote/course/list/$', vv.vote_course_list),
    (r'^vote/list/(\w+)/$', vv.vote_list),
    (r'^vote/detail/(\w+)/$', vv.vote_detail),
    (r'^vote/edit/(\w+)/$', vv.vote_edit),
    (r'^vote/add/(\w+)/$', vv.vote_add),
    (r'^vote/start/(\w+)/$', vv.vote_start),
    (r'^vote/end/(\w+)/$', vv.vote_end),
    (r'^vote/clear/(\w+)/$', vv.vote_clear),

    # ajax
    (r'^ajax/courseware_state/(\d+)/$', cv.courseware_state),
    (r'^ajax/courseware/upload/progress/(\w+)/$', cv.upload_progress),

    # media
    (r'^media/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.MEDIA_ROOT}),

    # Uncomment the admin/doc line below to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # (r'^admin/', include(admin.site.urls)),
)

urlpatterns += staticfiles_urlpatterns()
