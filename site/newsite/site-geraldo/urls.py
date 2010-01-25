# Copyright 2008 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.conf.urls.defaults import *

from gae_blog.feeds import LatestEntries

feeds = {
    'latest': LatestEntries,
}

urlpatterns = patterns('',
    # Admin
    url(r'^admin_user_required/$', 'views.admin_user_required', {}, 'admin_user_required'),
    url(r'^admin/gae_blog/', include('gae_blog.urls.admin')),
    url(r'^admin/gae_wiki/', include('gae_wiki.urls.admin')),
    url(r'^admin/gallery/', include('gallery.urls.admin')),
    url(r'^admin/update_cache/', 'views.admin_update_cache', {}, 'admin_update_cache'),
    url(r'^admin/', 'views.admin_index', {}, 'admin_index'),

    # Gallery
    url(r'^gallery/', include('gallery.urls.gallery')),

    # Blog
    url(r'^blog/', include('gae_blog.urls.blog')),

    # Feeds
    url(
        r'^feeds/(?P<url>.*)/$',
        'django.contrib.syndication.views.feed',
        {'feed_dict': feeds},
        ),

    # Special pages
    url(r'^contact/$', 'views.contact', {}, 'contact'),
    url(r'^robots.txt$', 'views.robots_txt', {}, 'robots_txt'),

    # Google Friends Connect
    url(
        r'^canvas.html$',
        'django.views.generic.simple.direct_to_template',
        {'template': 'friends_connect/canvas.html'},
        ),
    url(
        r'^rpc_relay.html$',
        'django.views.generic.simple.direct_to_template',
        {'template': 'friends_connect/rpc_relay.html'},
        ),

    # Wiki
    url(r'', include('gae_wiki.urls.wiki')),
)

