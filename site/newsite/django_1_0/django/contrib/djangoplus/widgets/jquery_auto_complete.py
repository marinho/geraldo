"""
Author: skam
Origin: http://www.djangosnippets.org/snippets/233/
"""

import types
from django import forms
from django.forms.widgets import flatatt
from django.forms.util import smart_unicode
from django.utils.html import escape
from django.utils.simplejson import JSONEncoder
from django.utils.safestring import mark_safe

class JQueryAutoComplete(forms.TextInput):
    attrs = {'autocomplete': 'off'}
    options = None

    def __init__(self, source, options={}, attrs={}, func_display=False):
        """source can be a list containing the autocomplete values or a
        string containing the url used for the XHR request.
        
        For available options see the autocomplete sample page::
        http://jquery.bassistance.de/autocomplete/"""
        
        self.source = source
        self.func_display = func_display

        if len(options) > 0:
            #self.options = JSONEncoder().encode(options)
            opt_list = []

            for k, v in options.items():
                opt = '"%s":'%k

                if k == 'select':
                    opt += v
                elif type(v) == types.StringType:
                    opt += '"%s"'%v
                else:
                    opt += JSONEncoder().encode(v)

                opt_list.append(opt)

            self.options = '{%s}'%(','.join(opt_list))
        
        self.attrs.update(attrs)
    
    def render_js(self, field_id):
        if isinstance(self.source, list):
            source = JSONEncoder().encode(self.source)
        elif isinstance(self.source, str):
            source = "'%s'" % escape(self.source)
        else:
            raise ValueError('source type is not valid')
        
        options = ''
        if self.options:
            options += ',%s' % self.options

        return u'$(\'#%s\').autocomplete(%s%s);' % (field_id, source, options)

    def render(self, name, value=None, attrs=None):
        final_attrs = self.build_attrs(attrs, name=name)
        if value:
            if self.func_display:
                final_attrs['value'] = self.func_display(value)
            else:
                final_attrs['value'] = escape(smart_unicode(value))

        if not self.attrs.has_key('id'):
            final_attrs['id'] = 'id_%s' % name    

        return mark_safe('<input type="text" %(attrs)s/> <script type="text/javascript" defer="defer"> %(js)s </script>' % {
                'attrs' : flatatt(final_attrs),
                'js' : self.render_js(final_attrs['id']),
                }
                )

