from google.appengine.api import users, images
from google.appengine.ext import db

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache, cache_page
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.core.urlresolvers import reverse
from django.core.cache import cache

from utils.decorators import page, admin_required
from utils.users import post_message
from utils.shortcuts import get_object_or_404

from models import Item
from forms import FormItem
import app_settings

@page('gallery/index.html')
def gallery_index(request):
    return locals()

@page('gallery/item_info.html')
def item_info(request, slug):
    item = get_object_or_404(Item, slug=slug)
    return locals()

def item_file(request, slug):
    item = cache.get(Item.get_cache_key(slug), None)

    if not item:
        item = get_object_or_404(Item, slug=slug)

        if item.cacheable:
            cache.set(Item.get_cache_key(slug), item, app_settings.GALLERY_CACHE_TIMEOUT)

    try:
        return HttpResponse(item.file, mimetype=item.mimetype)
    except:
        item = get_object_or_404(Item, slug=slug)
        return HttpResponse(item.file, mimetype=item.mimetype)

def item_thumb(request, slug):
    item = cache.get(Item.get_cache_key(slug), None)

    if not item:
        item = get_object_or_404(Item, slug=slug)

        if item.cacheable:
            cache.set(Item.get_thumb_cache_key(slug), item, app_settings.GALLERY_CACHE_TIMEOUT)
            
    return HttpResponse(item.thumb, mimetype=item.mimetype)

# Admin

@never_cache
@login_required
@admin_required
@page('admin/gallery/index.html')
def admin_index(request):
    list = Item.all()

    return locals()

@never_cache
@login_required
@admin_required
@page('admin/gallery/item/edit.html')
def admin_item_edit(request, id=None):
    item = id and Item.get_by_id(int(id)) or None

    if request.POST:
        form = FormItem(request.POST, files=request.FILES, instance=item)

        if form.is_valid():
            item = form.save(False)
            
            if form.cleaned_data.get('file_to_upload', None):
                # Get image to field file
                img = db.Blob(form.cleaned_data['file_to_upload'].read())
                item.file = img

                # Builds image thumbnail
                item.thumb = images.resize(img, 120, 120)

                item.mimetype = form.cleaned_data['file_to_upload'].content_type

            item.save()

            return HttpResponseRedirect(item.get_absolute_url())
    else:
        form = FormItem(instance=item)

    return locals()

@never_cache
@login_required
@admin_required
def admin_item_delete(request, id=None):
    item = id and Item.get_by_id(int(id)) or None

    if not item:
        raise Http404

    item.delete()

    post_message(request, 'Item deleted.')

    return HttpResponseRedirect(reverse('gallery.views.admin_index'))

