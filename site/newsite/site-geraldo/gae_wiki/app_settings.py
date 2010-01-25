from django.conf import settings

WIKI_CACHE_KEY_PREFIX = getattr(settings, 'WIKI_CACHE_KEY_PREFIX', 'wiki_')
WIKI_CACHE_TIMEOUT = getattr(settings, 'WIKI_CACHE_TIMEOUT', 60 * 60 * 24 * 30)

