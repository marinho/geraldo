from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('gallery.views',
    url(r'^$', 'admin_index', {}, 'admin_index'),

    # Wiki
    ##url(r'^item/$', 'admin_index', {}, 'admin_item_index'),
    url(r'^item/add/$', 'admin_item_edit', {}, 'admin_item_add'),
    url(r'^item/(?P<id>\d+)/$', 'admin_item_edit', {}, 'admin_item_edit'),
    url(r'^item/(?P<id>\d+)/delete/$', 'admin_item_delete', {}, 'admin_item_delete'),
)

