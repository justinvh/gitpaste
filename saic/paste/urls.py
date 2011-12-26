from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('saic.paste.views',
    url(r'^(?P<pk>\d+)/edit/$', 'paste_edit', name='paste_edit'),
    url(r'^(?P<pk>\d+)/download/$', 'paste_download', name='paste_download'),
    url(r'^(?P<pk>\d+)/$', 'paste_view', name='paste_view'),
    url(r'^find/$', 'find', name='find'),
    url(r'^$', 'paste', name='paste'),
)
