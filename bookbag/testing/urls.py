from django.conf.urls import patterns, url

import views


urlpatterns = patterns(
    '',
    url(r'^get/(\w)+/$', views.get_test),
    url(r'^result/put/$', views.put_result),
    url(r'^result/list/(\w+)/(personal|class)/$', views.result_list),
)
