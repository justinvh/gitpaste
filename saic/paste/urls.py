from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('saic.paste.views',
    url(r'^owner/(?P<owner>.+)/', 'user_pastes', name='user_pastes'),
    url(r'^(?P<pk>\d+)/adopt/$', 'paste_adopt', name='paste_adopt'),
    url(r'^(?P<pk>\d+)/edit/$', 'paste_edit', name='paste_edit'),
    url(r'^(?P<pk>\d+)/download/$', 'paste_download', name='paste_download'),
    url(r'^(?P<pk>\d+)/favorite/$', 'paste_favorite', name='paste_favorite'),
    url(r'^(?P<pk>\d+)/delete/$', 'paste_delete', name='paste_delete'),
    url(r'^commit/(?P<pk>.+)/adopt/$', 'commit_adopt', name='commit_adopt'),
    url(r'^users/', 'users', name='users'),
    url(r'^(?P<pk>\d+)/$', 'paste_view', name='paste_view'),
    url(r'^find/$', 'find', name='find'),
    url(r'^favorites/$', 'favorites', name='favorites'),
    url(r'^$', 'paste', name='paste'),
    url(r'^accounts/login/$', 'login', name='login'),
    url(r'^accounts/logout/$', 'logout', name='logout'),
    url(r'^accounts/register/$', 'register', name='register')
)
