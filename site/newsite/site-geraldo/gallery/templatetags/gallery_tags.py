import re
from google.appengine.ext import db

from django.template import Library
from django.utils.safestring import mark_safe

from gallery.models import Item

register = Library()

exp = re.compile('(\[%[ ]+gallery:(all|recent)\((.*?)\):([\d]+)[ ]+%\])')

@register.filter
def parse_gallery(text):
    chamadas = exp.findall(text)
    
    for expressao, func, args, count in chamadas:
        # Carrega lista de objetos
        lista = Item.all().filter('published =', True)

        fields_order = []
        tag = None

        # Interpreta argumentos de filtro
        if args:
            args_tmp = [a.split('=') for a in args.split(',')]

            for arg_l in args_tmp:
                arg = arg_l[0]
                val = len(arg_l) > 1 and arg_l[1] or True
                if val == 'False':
                    val = False
                elif val == 'True':
                    val = True

                if arg == 'tag':
                    lista = lista.filter('tags >=', val)
                    fields_order.append('tags')
                    tag = val
                else:
                    lista = lista.filter(arg+' =', val)
        
        # Interpreta funcao
        if func == 'all':
            fields_order.append('title')
        elif func == 'recent':
            fields_order.append('-pub_date')

        for field in fields_order:
            lista.order(field)

        if tag:
            lista = filter(lambda o: tag in o.tags, lista)

        # Monta HTML
        html_tmp = '<ul class="gallery_items">'
        for obj in lista[:int(count)]:
            html_tmp += '<li><a href="%s" title="%s"><img src="%s" alt="%s"/></a></li>'%(obj.get_file_url(), unicode(obj), obj.get_thumb_url(), unicode(obj))
        html_tmp += '</ul>'

        # Aplica resultado no texto
        text = text.replace(expressao, html_tmp)

    return mark_safe(text)

