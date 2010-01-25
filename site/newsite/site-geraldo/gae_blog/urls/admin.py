from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('gae_blog.views',
    url(r'^$', 'admin_index', {}, 'admin_index'),

    # Wiki
    #url(r'^entry/$', 'admin_index', {}, 'admin_index'),
    url(r'^entry/add/$', 'admin_entry_edit', {}, 'admin_entry_add'),
    url(r'^entry/import/$', 'admin_entry_import', {}, 'admin_entry_import'),
    #url(r'^entry/export/$', 'admin_entry_export_all', {}, 'admin_export_all'),
    url(r'^entry/(?P<id>\d+)/$', 'admin_entry_edit', {}, 'admin_edit'),
    url(r'^entry/(?P<id>\d+)/delete/$', 'admin_entry_delete', {}, 'admin_delete'),
)

