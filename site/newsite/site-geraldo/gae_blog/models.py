from appengine_django.models import BaseModel
from google.appengine.ext import db

from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.core.cache import cache
from django.contrib.markup.templatetags.markup import markdown

from utils.custom_models import CustomModel

import app_settings

class Entry(CustomModel):
    title = db.StringProperty()
    slug = db.StringProperty()
    pub_date = db.DateTimeProperty(auto_now_add=True)
    description = db.TextProperty()
    text = db.TextProperty()
    tags = db.ListProperty(db.Category)
    format = db.CategoryProperty()
    published = db.BooleanProperty(default=False)
    author = db.UserProperty()
    template = db.StringProperty()
    show_in_rss = db.BooleanProperty(default=False)
    cacheable = db.BooleanProperty(default=True)
    sequence = db.IntegerProperty()
    old_id = db.IntegerProperty()
    disable_comments = db.BooleanProperty(default=False)

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('entry', args=[self.slug])

    def put(self):
        if not self.slug:
            self.slug = unicode(slugify(self.title))

        # Delete from cache
        cache.delete(Entry.get_cache_key(self.slug))

        return super(Entry, self).put()

    @classmethod
    def get_cache_key(cls, slug):
        return app_settings.BLOG_CACHE_KEY_PREFIX + slug

    def description_or_text(self):
        return self.description or self.text[:200]+'...'

    @classmethod
    def latest(cls):
        l = cls.all().filter('published =', True)
        l.order('-pub_date')

    def get_text(self):
        if self.format == 'markdown':
            return markdown(self.text)
        elif self.format == 'textile':
            return textile(self.text)
        
        return self.text

