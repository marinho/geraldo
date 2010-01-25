# -*- coding: utf-8 -*-
from django.forms import widgets
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.utils.datastructures import MultiValueDict
from django.http import HttpResponse
from django.forms.util import flatatt
from django.utils.encoding import force_unicode
from django.conf import settings
from django.views.decorators.cache import never_cache

# id="ajaxmultiselect_field_%(name)s"
# style="padding: 5px; margin-left: 105px;"
TPL_UL = """
<ul class="ajaxmultiselect_field" %(attrs)s>
    %(items)s
</ul>
"""

TPL_LI = """
<li id="li_%(name)s_%(id)d">
    %(repr)s <img src="/admin_media/img/admin/icon_deletelink.gif" class="ajaxmultiselect_remove"/>
    <input type="hidden" name="%(name)s" value="%(id)d"/>
</li>
"""

TPL_LI_ADD = """
<li id="li_%(name)s_add">
    <input id="ajaxmultiselect_input_%(name)s_add" autocomplete="off" class="ajaxmultiselect_add"/>
    <script type="text/javascript" defer="defer">
        AUTO_TEMP_ID_%(name)s = '';

        function onSelect(data) {
            AUTO_TEMP_ID_%(name)s = data.id;
        }

        $('input#ajaxmultiselect_input_%(name)s_add').autocomplete(
            "%(url)s",
            {
                "autoFill": true,
                "multiple": false,
                "select": onSelect,
                "minChars": 0,
                "scroll": false
            }
        );
    </script>

    <img src="/admin_media/img/admin/icon_addlink.gif" class="ajaxmultiselect_add"/>
</li>
"""

TPL_SCRIPT = """
<script type="text/javascript" defer="defer">
    $('ul#id_%(name)s>li>img.ajaxmultiselect_add').click(function(){
        if (!AUTO_TEMP_ID_%(name)s) {
            alert('You must choose a valid item!');
            return
        } else if (document.getElementById("li_%(name)s_"+AUTO_TEMP_ID_%(name)s)) {
            alert('You already added this!');
            return
        }

        var li = document.createElement('li');
        li.id = "li_%(name)s_"+AUTO_TEMP_ID_%(name)s;

        var txt = document.createTextNode($('#ajaxmultiselect_input_%(name)s_add').val());
        li.appendChild(txt);

        var img = document.createElement('img');
        img.src = "/admin_media/img/admin/icon_deletelink.gif";
        img.className = "ajaxmultiselect_remove";
        li.appendChild(img);

        var inp = document.createElement('input');
        inp.type = "hidden";
        inp.name = "%(name)s"
        inp.value = AUTO_TEMP_ID_%(name)s;
        li.appendChild(inp);

        document.getElementById('id_%(name)s').insertBefore(li, document.getElementById('li_%(name)s_add'))

        $('ul#id_%(name)s>li>img.ajaxmultiselect_remove').click(ajaxMultiSelectRemove);
    });

    function ajaxMultiSelectRemove() {
        $(this).parent().remove();
    }

    $('ul#id_%(name)s>li>img.ajaxmultiselect_remove').click(ajaxMultiSelectRemove);
</script>
"""

class AjaxMultiSelect(widgets.Widget):
    model = None
    auto_url = None

    class Media:
        js = (settings.MEDIA_URL+'js/jquery-packed.js',
              settings.MEDIA_URL+'js/jquery.autocomplete.js',
              settings.MEDIA_URL+'js/jquery.bgiframe.min.js',)
        css = {'all':
                (settings.MEDIA_URL+'css/jquery.autocomplete.css',
                 settings.MEDIA_URL+'css/ajax_m2m_widget.css',)
                }

    def __init__(self, verbose_name, model, auto_url, attrs=None):
        self.verbose_name = verbose_name
        self.model = model
        self.auto_url = auto_url

        super(AjaxMultiSelect, self).__init__(attrs)

    def build_attrs(self, extra_attrs=None, **kwargs):
        ret = super(AjaxMultiSelect, self).build_attrs(extra_attrs=None, **kwargs)

        if 'style' in ret:
            ret['style'] += 'padding: 5px; '
        else:
            ret['style'] = 'padding: 5px; '

        return ret

    def render(self, name, value, attrs=None, choices=()):
        final_attrs = self.build_attrs(attrs)
        final_attrs.setdefault('id', 'id_'+name)

        if value:
            items = []
            
            for id in value:
                try:
                    items.append(self.model.objects.get(id=id))
                except self.model.DoesNotExist, e:
                    pass
        else:
            items = []
        
        li_items = '\n'.join([TPL_LI %{'name': name, 'id': item.id, 'repr': unicode(item)} for item in items])
        li_add = TPL_LI_ADD %{'name': name, 'url': self.auto_url}

        output = []
        output.append(TPL_UL %{'name': name , 'items': '\n'.join((li_items, li_add)), 'attrs': flatatt(final_attrs)})
        output.append(TPL_SCRIPT %{'name': name, 'url': self.auto_url})

        return mark_safe(u'\n'.join(output))

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            return data.getlist(name)
        return data.get(name, None)

@never_cache
def auto_complete_view(request, query_func, desc_field, id_field, limit=15, show_empty=True, extra_args=False):
    def iter_results(results):
        if results:
            for r in results:
                #yield '%s|%s\n' % (desc_field and getattr(r, desc_field) or unicode(r), getattr(r, id_field))
                yield unicode('%s|%s\n' % (desc_field and getattr(r, desc_field) or unicode(r), getattr(r, id_field)))
    
    if not show_empty and not request.GET.get('q'):
        return HttpResponse(mimetype='text/plain')
    
    q = request.GET.get('q', '')

    if extra_args:
        args = dict(request.GET.items())
        items = query_func(q, args)[:limit]
    else:
        items = query_func(q)[:limit]

    res = iter_results(items)

    return HttpResponse([x for x in res], mimetype='text/plain')

