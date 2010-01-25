from appengine_django.models import BaseModel
from google.appengine.ext import db

from django.template.defaultfilters import slugify
from django.core.urlresolvers import reverse
from django.core.cache import cache

from utils.custom_models import CustomModel

import app_settings

class Item(CustomModel):
    title = db.StringProperty()
    slug = db.StringProperty()
    pub_date = db.DateTimeProperty(auto_now_add=True)
    file = db.BlobProperty()
    thumb = db.BlobProperty()
    mimetype = db.StringProperty()
    cacheable = db.BooleanProperty(default=True)
    old_id = db.IntegerProperty()
    published = db.BooleanProperty(default=False)
    tags = db.ListProperty(db.Category)

    def put(self):
        if not self.slug:
            self.slug = unicode(slugify(self.title))

        # Delete from cache
        cache.delete(Item.get_cache_key(self.slug))
        cache.delete(Item.get_thumb_cache_key(self.slug))

        return super(Item, self).put()

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        return '/gallery/%s/'%self.slug

    def get_file_url(self):
        return '/gallery/%s/file/'%self.slug

    def get_thumb_url(self):
        return '/gallery/%s/thumb/'%self.slug

    @classmethod
    def get_cache_key(cls, slug):
        return app_settings.GALLERY_CACHE_KEY_PREFIX + slug

    @classmethod
    def get_thumb_cache_key(cls, slug):
        return app_settings.GALLERY_CACHE_KEY_PREFIX + 'thumb_' + slug

