# -*- coding: utf-8 -*-
from django.contrib.syndication.feeds import Feed

from models import Wiki

class LatestEntries(Feed):
    title = u'Aprendendo Django no Planeta Terra'
    link = 'http://aprendendodjango.com/'
    description = u'Capítulos do livro eletrônico "Aprendendo Django no Planeta Terra"'

    def items(self):
        return Wiki.all().order('-pub_date').filter('show_in_rss =', True)[:10]

    def item_pubdate(self, item):
        return item.pub_date

