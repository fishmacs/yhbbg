from django.conf.urls import patterns, url

import views


urlpatterns = patterns(
    '',
    url(r'^get/(\w)+/$', views.get_test)
)