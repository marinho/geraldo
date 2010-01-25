from django import forms
from django.forms.forms import BoundField
from django.utils.html import escape
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

class SectionedForm(object):
    """
    ToDo
    """
    sections = {}
    section_template = "<h3>%s</h3>"

    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
        "Helper function for outputting HTML. Used by as_table(), as_ul(), as_p()."
        top_errors = self.non_field_errors() # Errors that should be displayed above all fields.
        output, hidden_fields = [], []

        for section, fields in self.sections:
            if section:
                output.append(normal_row % {'errors': '', 'label': '&nbsp;', 'field': self.section_template%section, 'help_text': ''})

            for name, field in [i for i in self.fields.items() if i[0] in fields]:
                bf = BoundField(self, field, name)
                bf_errors = self.error_class([escape(error) for error in bf.errors]) # Escape and cache in local variable.
                if bf.is_hidden:
                    if bf_errors:
                        top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
                    hidden_fields.append(unicode(bf))
                else:
                    if errors_on_separate_row and bf_errors:
                        output.append(error_row % force_unicode(bf_errors))
                    if bf.label:
                        label = escape(force_unicode(bf.label))
                        # Only add the suffix if the label does not end in
                        # punctuation.
                        if self.label_suffix:
                            if label[-1] not in ':?.!':
                                label += self.label_suffix
                        label = bf.label_tag(label) or ''
                    else:
                        label = ''
                    if field.help_text:
                        help_text = help_text_html % force_unicode(field.help_text)
                    else:
                        help_text = u''
                    output.append(normal_row % {'errors': force_unicode(bf_errors), 'label': force_unicode(label), 'field': unicode(bf), 'help_text': help_text})

        if top_errors:
            output.insert(0, error_row % force_unicode(top_errors))
        if hidden_fields: # Insert any hidden fields in the last row.
            str_hidden = u''.join(hidden_fields)
            if output:
                last_row = output[-1]
                # Chop off the trailing row_ender (e.g. '</td></tr>') and
                # insert the hidden fields.
                output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
            else:
                # If there aren't any rows in the output, just append the
                # hidden fields.
                output.append(str_hidden)
        return mark_safe(u'\n'.join(output))

