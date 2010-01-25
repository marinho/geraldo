from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.api.datastore_errors import NeedIndexError

from django.conf import settings

from gae_blog.models import Entry
from gae_wiki.models import Wiki

def gae(request):
    global messages_pool

    ret = {}

    #ret['user'] = users.get_current_user()
    ret['user_is_current_user_admin'] = users.is_current_user_admin()
    ret['logout_url'] = users.create_logout_url('/')
    ret['MEDIA_URL'] = settings.MEDIA_URL

    try:
        ret['messages'] = request.session['messages_pool']
        request.session['messages_pool'] = []
    except:
        ret['messages'] = []

    ret['html_lateral'] = Wiki.get_by_field('slug', 'lateral')
    ret['html_lateral'] = ret['html_lateral'] and ret['html_lateral'].render() or ''

    ret['html_postit'] = Wiki.get_by_field('slug', 'postit')
    ret['html_postit'] = ret['html_postit'] and ret['html_postit'].render() or ''

    return ret

def blog(request):
    ret = {}

    recent_entries = Entry.all().filter('published =', True)
    recent_entries.order('-pub_date')

    try:
        ret['recent_entries'] = recent_entries[:5]
    except NeedIndexError:
        pass

    ret['tags'] = ['django','python']

    return ret

