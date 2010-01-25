from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('gallery.views',
    url(r'^$', 'gallery_index', {}, 'galery_index'),

    # Item
    url(r'^(?P<slug>[\w_-]+)/$', 'item_info', {}, 'item_info'),
    url(r'^(?P<slug>[\w_-]+)/file/$', 'item_file', {}, 'item_file'),
    url(r'^(?P<slug>[\w_-]+)/thumb/$', 'item_thumb', {}, 'item_thumb'),
)


