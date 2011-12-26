from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('saic.paste.views',
    url(r'^', 'paste', name='paste'),
)
