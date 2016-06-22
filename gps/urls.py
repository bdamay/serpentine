from django.conf.urls import  include, url
from django.http import HttpResponse
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
                       #APPLICATION gps
                       url(r'^$', views.index),
                       url(r'^recherche/$', views.recherche),
                       url(r'^samples/$', views.samples),
                       #gpx file
                       url(r'^trace/(\d+).gpx', views.gpx),
                       #view_trace html
                       url(r'^trace/(?P<num>\d+)$', views.view_trace),
                       url(r'^traceinfo/(\d+)', views.trace_info_html),
                       url(r'^traceshortinfo/(\d+)', views.trace_short_info_html),
                       url(r'^tracetabs/(traces(?:/\d+)+)?/(segment(?:/\d+)+)?', views.trace_tabs_html),
                       url(r'^tracestats/(\d+)', views.trace_stats),
                       #records
                       url(r'^records/$', views.records),
                       #blocks html (nav ... )
                       url(r'^nav.html', views.nav_html),
                       url(r'^nearby.html', views.nearby),
                       #edit tracks
                       url(r'^edit/(\d+)', views.edit),
                       #upload files
                       url(r'^upload/$', views.upload),
                       url(r'^modify/$', views.modify),
                       #login logout register
                       url(r'^accounts/login/$', auth_views.login, {'template_name': 'gps/login.html'}),
                       url(r'^logout/$', views.logout),
                       url(r'^login/$', views.login),
                       url(r'^register/$', views.register),
                       #JSON urls (usuall called with track number ?t=N)
                       url(r'^trace/json$', views.trace_json),
                       url(r'^trace/json_info$', views.trace_json_info),
                       url(r'^trace/json_index$', views.trace_json_index),
                       #User urls
                       url(r'^user/records/$', views.user_records),
                       url(r'^user/profile$', views.user_profile),
                       #JSON urls (called with track number ?t=N&t2=...)
                       url(r'^trace/json_segments$', views.trace_segment_json),
                       #ajax cookies
                       url(r'^setmaptype/(?P<maptype>ol|ign)', views.set_maptype),
                       #tests
                       url(r'^test_cookies', views.test_cookies),
                       url(r'^test_ign', views.test_ign),
                       #robots deny
                       url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", mimetype="text/plain")),
]
