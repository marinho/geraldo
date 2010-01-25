from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('gae_wiki.views',
    url(r'^$', 'admin_index', {}, 'admin_index'),

    # Wiki
    #url(r'^wiki/$', 'admin_index', {}, 'admin_index'),
    url(r'^wiki/add/$', 'admin_wiki_edit', {}, 'admin_add'),
    url(r'^wiki/export/$', 'admin_wiki_export_all', {}, 'admin_export_all'),
    url(r'^wiki/(?P<id>\d+)/$', 'admin_wiki_edit', {}, 'admin_edit'),
    url(r'^wiki/(?P<id>\d+)/delete/$', 'admin_wiki_delete', {}, 'admin_delete'),
)

