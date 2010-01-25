from google.appengine.api import users

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views.decorators.cache import cache_page, never_cache
from django.core.cache import cache
from django.template.loader import render_to_string

from utils.decorators import page, admin_required
from utils.shortcuts import get_object_or_404
from utils.serialization import serialize

from models import Wiki
from forms import FormWiki

import app_settings

#@cache_page(60)
def wiki(request, slug):
    ret = cache.get(Wiki.get_cache_key(slug), None)

    if not ret:
        wiki = get_object_or_404(Wiki, slug=slug)
        tpl = wiki.template or 'gae_wiki/wiki.html'

        ret = render_to_response(
            tpl,
            locals(),
            context_instance=RequestContext(request),
            )
        ret = ret._get_content()

        if wiki.cacheable:
            cache.set(Wiki.get_cache_key(slug), ret, app_settings.WIKI_CACHE_TIMEOUT)

    return HttpResponse(ret)

@page('gae_wiki/sequence.html')
def wiki_sequence(request):
    wikis = Wiki.all().order('sequence').filter('show_in_rss =', True)
    return locals()

# Admin

@login_required
@admin_required
@page('admin/gae_wiki/index.html')
def admin_index(request):
    list = Wiki.all()

    return locals()

@never_cache
@login_required
@admin_required
@page('admin/gae_wiki/wiki/edit.html')
def admin_wiki_edit(request, id=None):
    wiki = id and Wiki.get_by_id(int(id)) or None

    if request.POST:
        form = FormWiki(request.POST, files=request.FILES, instance=wiki)

        if form.is_valid():
            wiki = form.save(False)
            wiki.author = users.get_current_user()
            wiki.save()

            return HttpResponseRedirect(reverse('gae_wiki.views.admin_index'))
    else:
        form = FormWiki(instance=wiki)

    return locals()

@never_cache
@login_required
@admin_required
def admin_wiki_delete(request, id=None):
    wiki = id and Wiki.get_by_id(int(id)) or None

    if not wiki:
        raise Http404

    wiki.delete()

    return HttpResponseRedirect('/admin/gae_wiki/')

@never_cache
@login_required
@admin_required
def admin_wiki_export_all(request):
    items = Wiki.all().order('title')
    #ret = render_to_string('gae_wiki/export_all.txt', locals())
    ret = serialize(items)
    return HttpResponse(ret, mimetype='text/xml')

