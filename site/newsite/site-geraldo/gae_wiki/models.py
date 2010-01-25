from appengine_django.models import BaseModel
from google.appengine.ext import db

from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.core.cache import cache
from django.template.loader import render_to_string

from utils.custom_models import CustomModel

import app_settings

class Wiki(CustomModel):
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
        return reverse('wiki', args=[self.slug])

    def put(self):
        if not self.slug:
            self.slug = unicode(slugify(self.title))

        # Delete from cache
        cache.delete(Wiki.get_cache_key(self.slug))

        return super(Wiki, self).put()

    @classmethod
    def get_cache_key(cls, slug):
        return app_settings.WIKI_CACHE_KEY_PREFIX + slug

    def description_or_text(self):
        return self.description or self.text

    def render(self):
        return render_to_string('gae_wiki/render_wiki.html', {'wiki': self})

