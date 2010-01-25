# -*- coding: utf-8 -*-
from django.forms import widgets
from django.utils.safestring import mark_safe
from django.utils.datastructures import MultiValueDict
from django.forms.util import flatatt

TPL_OPTION = """<option value="%(value)s" %(selected)s>%(desc)s</option>"""

TPL_SELECT = """
<select class="dropdown_select" %(attrs)s>
%(opts)s
</select>
"""

TPL_SCRIPT = """
<script type="text/javascript" defer="defer">
    $('span#%(id)s>select.dropdown_select').change(function(){
        var pattern = 'span#%(id)s>select.dropdown_select';
        var last_item = $(pattern+':last');

        if (last_item.val()) {
            last_item.clone(true).appendTo($('span#%(id)s'));
            $('span#%(id)s').append(' ');
        };

        var values = [];

        for (var i=$(pattern).length-1; i>=0; i--) {
            if (values.indexOf($($(pattern).get(i)).val()) >= 0) {
                $($(pattern).get(i)).remove();
            } else {
                values.push($($(pattern).get(i)).val());
            }
        };
    });
</script>
"""

TPL_FULL = """
<span class="dropdown_multiple" id="%(id)s">
%(values)s
%(script)s
</span>
"""

class DropDownMultiple(widgets.Widget):
    choices = None

    def __init__(self, attrs=None, choices=()):
        self.choices = choices

        super(DropDownMultiple, self).__init__(attrs)

    def render(self, name, value, attrs=None, choices=()):
        if value is None: value = []
        final_attrs = self.build_attrs(attrs, name=name)

        # Pop id
        id = final_attrs['id']
        del final_attrs['id']

        # Insert blank value
        choices = [('','---')] + list(self.choices)

        # Build values
        items = []
        for val in value:
            opts = "\n".join([TPL_OPTION %{'value': k, 'desc': v, 'selected': val == k and 'selected="selected"' or ''} for k, v in choices])
            
            items.append(TPL_SELECT %{'attrs': flatatt(final_attrs), 'opts': opts})

        # Build blank value
        opts = "\n".join([TPL_OPTION %{'value': k, 'desc': v, 'selected': ''} for k, v in choices])
        items.append(TPL_SELECT %{'attrs': flatatt(final_attrs), 'opts': opts})

        script = TPL_SCRIPT %{'id': id}
        output = TPL_FULL %{'id': id, 'values': '\n'.join(items), 'script': script}

        return mark_safe(output)

    def value_from_datadict(self, data, files, name):
        if isinstance(data, MultiValueDict):
            return [i for i in data.getlist(name) if i]
        
        return data.get(name, None)

