from django.conf import settings

BLOG_CACHE_KEY_PREFIX = getattr(settings, 'BLOG_CACHE_KEY_PREFIX', 'blog_')
BLOG_CACHE_TIMEOUT = getattr(settings, 'BLOG_CACHE_TIMEOUT', 60 * 60 * 24 * 30)

