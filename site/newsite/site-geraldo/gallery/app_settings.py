from django.conf import settings

GALLERY_CACHE_KEY_PREFIX = getattr(settings, 'GALLERY_CACHE_KEY_PREFIX', 'wiki_')
GALLERY_CACHE_TIMEOUT = getattr(settings, 'GALLERY_CACHE_TIMEOUT', 60 * 60 * 24 * 30)

