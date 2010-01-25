# -*- coding: utf-8 -*-
from django.contrib.syndication.feeds import Feed

from models import Entry

class LatestEntries(Feed):
    title = u'Geraldo Reports'
    link = 'http://www.geraldoreports.org/'
    description = u'Latest blog entries from Geraldo Reports blog'

    def items(self):
        return Entry.all().order('-pub_date').filter('show_in_rss =', True)[:10]

    def item_pubdate(self, item):
        return item.pub_date

