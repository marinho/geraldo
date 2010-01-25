import datetime
from google.appengine.api import users

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page, never_cache
from django.core.cache import cache
from django.template.loader import render_to_string
from django.utils import feedgenerator
from django.conf import settings

from utils.decorators import page, admin_required
from utils.shortcuts import get_object_or_404
from utils.serialization import serialize

from models import Entry
from forms import FormEntry, FormImport

import app_settings

@page('gae_blog/index.html')
def entry_index(request):
    _posts = Entry.all().filter('published =', True)
    _posts.order('-pub_date')
    _posts = list(_posts)

    try:
        latest = _posts[0]
    except IndexError:
        latest = None

    posts = len(_posts) > 1 and _posts[1:11] or []

    return locals()

#@cache_page(60)
def entry(request, slug):
    ret = cache.get(Entry.get_cache_key(slug), None)

    if not ret:
        entry = get_object_or_404(Entry, slug=slug)
        tpl = entry.template or 'gae_blog/entry.html'

        ret = render_to_response(
            tpl,
            locals(),
            context_instance=RequestContext(request),
            )
        ret = ret._get_content()

        if entry.cacheable:
            cache.set(Entry.get_cache_key(slug), ret, app_settings.BLOG_CACHE_TIMEOUT)

    return HttpResponse(ret)

def entry_by_old_id(request, old_id):
    entry = get_object_or_404(Entry, old_id=int(old_id))
    return HttpResponseRedirect(entry.get_absolute_url())

@page('gae_blog/tag_index.html')
def tag_index(request, tag):
    posts = Entry.all().filter('published =', True).filter('tags =',tag)
    posts.order('-pub_date')
    posts = [i for i in posts]

    if not posts:
        raise Http404

    latest = posts[0]

    try:
        posts = posts[1:]
    except ValueError:
        posts = []

    return locals()

@page('gae_blog/year_index.html')
def year_index(request, year):
    start_date = datetime.datetime(int(year),1,1)
    end_date = datetime.datetime(int(year),12,31)

    posts = Entry.all().filter('published =', True)#.filter('pub_date >=',start_date).filter('pub_date <=',end_date)
    posts.order('-pub_date')
    posts = [i for i in posts]

    if not posts:
        raise Http404

    latest = posts[0]

    try:
        posts = posts[1:]
    except ValueError:
        posts = []

    return locals()

def feeds_tag(request, tag):
    lang = "pt-br"

    feed = feedgenerator.Rss201rev2Feed(
            title = u'Django Utilidades :: Marinho Brandao',
            link = settings.PROJECT_ROOT_URL,
            description = u'',
            language = lang,
            )

    entries = Entry.all().filter('published =',True).filter('show_in_rss =',True).filter('tags =',tag)
    entries.order('-pub_date')
    entries = entries[:20]

    for e in entries:
        feed.add_item(
                title=e.title,
                link=settings.PROJECT_ROOT_URL[:-1]+e.get_absolute_url(),
                description=e.get_text(),
                )

    response = HttpResponse(mimetype="application/xhtml+xml")
    feed.write(response, 'utf-8')
    return response

# Admin

@login_required
@admin_required
@page('admin/gae_blog/index.html')
def admin_index(request):
    list = Entry.all()
    list.order('-pub_date')

    return locals()

@never_cache
@login_required
@admin_required
@page('admin/gae_blog/entry/edit.html')
def admin_entry_edit(request, id=None):
    entry = id and Entry.get_by_id(int(id)) or None

    if request.POST:
        form = FormEntry(request.POST, files=request.FILES, instance=entry)

        if form.is_valid():
            entry = form.save(False)
            entry.author = users.get_current_user()
            entry.save()

            return HttpResponseRedirect(reverse('admin_index'))
    else:
        form = FormEntry(instance=entry)

    return locals()

@never_cache
@login_required
@admin_required
def admin_entry_delete(request, id=None):
    entry = id and Entry.get_by_id(int(id)) or None

    if not entry:
        raise Http404

    entry.delete()

    return HttpResponseRedirect('/admin/gae_blog/')

@never_cache
@login_required
@admin_required
def admin_entry_export_all(request):
    items = Entry.all().order('title')
    #ret = render_to_string('gae_blog/export_all.txt', locals())
    ret = serialize(items)
    return HttpResponse(ret, mimetype='text/xml')

@never_cache
@login_required
@admin_required
@page('admin/gae_blog/entry/import.html')
def admin_entry_import(request):
    if request.method == 'POST':
        form = FormImport(request.POST, files=request.FILES)

        if form.is_valid():
            form.do_import()
    else:
        form = FormImport()

    return locals()

