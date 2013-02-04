from django.conf.urls import patterns, url

urlpatterns = patterns('paste.views',
    url(r'^paste/$', 'paste_new', name='paste_new'),
    url(r'^paste/(?P<pk>\d+)/$', 'paste_view', name='paste_view'),
)
