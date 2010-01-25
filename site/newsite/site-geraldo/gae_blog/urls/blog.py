from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('gae_blog.views',
    url(r'^$', 'entry_index', {}, 'entry_index'),
    url(r'^rss/(?P<tag>[\w_-]+)/$', 'feeds_tag', {}, 'feeds_tag'),
    url(r'^(?P<year>\d{4})/$', 'year_index', {}, 'year_index'),
    url(r'^(?P<slug>[\w_-]+)/$', 'entry', {}, 'entry'),
    url(r'^p/(?P<old_id>\d+)/$', 'entry_by_old_id', {}, 'entry_by_old_id'),
    url(r'^tags/(?P<tag>[\w_-]+)/$', 'tag_index', {}, 'tag_index'),
)

