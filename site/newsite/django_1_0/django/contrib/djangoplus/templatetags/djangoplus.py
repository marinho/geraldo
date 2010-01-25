import base64, types
from datetime import datetime, timedelta

from django import template
from django.template import Library, Node
from django.utils.translation import ugettext as _
from django.conf import settings
from django.template.defaultfilters import slugify

register = Library()

"""
Boolean general utilities
"""

@register.filter
def multiple_of(value,arg):
    # Semelhante ao divisibleby, porem, testa multiplos
    return value % arg == 0

@register.filter
def in_list(value,arg):
    if not value:
        return False

    # Verifica se um item estah contido noutro
    if type(arg) == types.StringType:
        return value in arg.split(',')
    else:
        return value in arg

@register.filter
def is_equal(value,arg):
    # Recurso ideal para aposentra o infame ifequal - nao funciona em caso de tipos diferentes
    return value == arg

@register.filter
def is_not_equal(value,arg):
    # O inverso do is_equal
    return value != arg

@register.filter
def is_lt(value,arg):
    # A mesma coisa do is_equal, porem, testa "lower than"
    return int(value) < int(arg)

@register.filter
def is_lte(value,arg):
    # A mesma coisa do is_equal, porem, testa "lower than or equal"
    return int(value) <= int(arg)

@register.filter
def is_gt(value,arg):
    # A mesma coisa do is_equal, porem, testa "greater than"
    return int(value) > int(arg)

@register.filter
def is_gte(value,arg):
    # A mesma coisa do is_equal, porem, testa "greater than or equal"
    return int(value) >= int(arg)

"""
Date/time util template filters
"""

@register.filter
def is_day_of(value,arg):
    return (arg and value) and arg.day == int(value)

@register.filter
def is_month_of(value,arg):
    return (arg and value) and arg.month == int(value)

@register.filter
def is_year_of(value,arg):
    return (arg and value) and arg.year == int(value)

@register.filter
def is_hour_of(value,arg):
    return (arg and value) and arg.hour == int(value)

@register.filter
def is_minute_of(value,arg):
    return (arg and value) and arg.minute == int(value)

@register.filter
def dec_year(value,arg):
    delta = type(arg) != types.IntType and int(arg) or arg
    return value - timedelta(365 * delta)

@register.filter
def dec_month(value,arg):
    delta = type(arg) != types.IntType and int(arg) or arg
    return value - timedelta(30 * delta)

@register.filter
def inc_year(value,arg):
    delta = type(arg) != types.IntType and int(arg) or arg
    return value + timedelta(365 * delta)

@register.filter
def inc_month(value,arg):
    delta = type(arg) != types.IntType and int(arg) or arg
    return value + timedelta(30 * delta)

@register.filter
def list_as_text(value, field=None):
    if field:
        def get_value(obj, attr):
            attr = getattr(obj, attr)

            if type(attr) == types.MethodType:
                return attr()

            return attr or ''

        return ', '.join([get_value(i, field) for i in value])
    else:
        return ', '.join([unicode(i) for i in value])

@register.filter
def list_as_links(value):
    return ', '.join(['<a href="%s">%s</a>'%(i.get_absolute_url(), unicode(i)) for i in value])

"""
reStructuredText
"""

@register.filter
def rest(value, arg):
    from docutils.core import publish_parts

    arg = arg or 'html'
    parts = publish_parts(value, writer_name=arg)
    return parts['html_body']

"""
Miscelanea
"""

def multifind(s, q):
    # Retorna uma lista de posicoes de uma string em outra - utilizado pelo highlight
    ret = []
    sl = s.lower()
    q = q.lower()
    i = 0

    while i < len(sl):
        aux = sl[i:]
        if aux.find(q) == 0:
            ret.append(i)
            i += len(q)
        else:
            i += 1

    return ret

@register.filter
def highlight(s, q):
    # Destaca uma string dentro de outra em case insensitive, respeitando valor original
    pos = multifind(s, q)

    if not pos: return s

    anterior = 0
    ret = ''
    
    for p in pos:
        if anterior:
            ret += s[anterior+len(q):p]
        else:
            ret += s[anterior:p]

        ret += '<span class="highlight">' + s[p:p+len(q)] + '</span>'
        anterior = p

    ret += s[p+len(q):]

    return ret

@register.filter_function
def attr(obj, arg1):
    att, value = arg1.split("=")
    obj.field.widget.attrs[att] = value
    return obj

@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)

"""
TAMPLATE TAGS
"""

class ProtectAntiRobotsNode(Node):
    phrase = ''
    nodelist = ''

    def __init__(self, nodelist, phrase=None):
        super(ProtectAntiRobotsNode, self).__init__()

        self.nodelist = nodelist
        self.phrase = phrase or _('Let us know if you are human')

    def __repr__(self):
        return "<ProtectAntiRobotsNode>"

    def render(self, context):
        request = context['request']
        path = slugify(request.get_full_path())
        if 'protectantirobots_sec_'+path in request.COOKIES and \
           'protectantirobots_key_'+path in request.COOKIES:
            if request.COOKIES['protectantirobots_sec_'+path] == base64.b64decode(request.COOKIES['protectantirobots_key_'+path]):
                output = self.nodelist.render(context)
                return output
        
        sec = base64.b64encode(datetime.now().strftime("%H%m%S"))
        return '<a href="%s">%s</a>' %(self.get_url(sec, path), self.phrase)

    def get_url(self, sec, path):
        return "/protectantirobots/?k=%s&path=%s"%(sec, path)

def do_protectantirobots(parser, token):
    nodelist = parser.parse(('endprotectantirobots',))
    parser.delete_first_token()

    parts = token.split_contents()
    phrase = len(parts) > 1 and parts[1][1:-1] or None

    return ProtectAntiRobotsNode(nodelist, phrase)
do_protectantirobots= register.tag('protectantirobots', do_protectantirobots)

"""
{% dynamic_template [group] "name" %}
"""

from django.contrib.djangoplus.models import DynamicTemplate

class DynamicTemplateRender(template.Node):
    slug = None
    is_group = False

    def __init__(self, slug, is_group=False):
        self.slug = slug
        self.is_group = is_group

    def render(self, context):
        ret = ''

        if self.is_group:
            templates = DynamicTemplate.objects.filter(group=self.slug)
        else:
            templates = DynamicTemplate.objects.filter(slug=self.slug)

        for tpl in templates:
            ret += tpl.render(context)

        return ret

def do_dynamic_template(parser, token):
    try:
        parts = token.split_contents()
        tag_name = parts[0]
        slug = parts[-1]

        if len(parts) > 3:
            raise ValueError('Many arguments')
        elif len(parts) > 2 and parts[1] == 'group':
            is_group = True
        else:
            is_group = False
    except ValueError, e:
        raise template.TemplateSyntaxError, "%s requires 1 or 2 arguments" \
                % token.contents.split()[0]

    return DynamicTemplateRender(slugify(slug), is_group)

register.tag('dynamic_template', do_dynamic_template)

