from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('gae_wiki.views',
    url(r'^$', 'wiki', {'slug': 'index'}, 'wiki_index'),
    url(r'^sequence/$', 'wiki_sequence', {}, 'wiki_sequence'),
    url(r'^(?P<slug>[\w_/-]+)/$', 'wiki', {}, 'wiki'),
)

