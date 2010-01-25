from django import forms
from django.utils.safestring import mark_safe

class ModelRawIdWidget(forms.TextInput):
    """
    A Widget for displaying ForeignKeys in the "raw_id" interface rather than
    in a <select> box.
    """
    def __init__(self, model, limit_choices_to=None, attrs=None):
        self.model = model
        self.limit_choices_to = limit_choices_to
        super(ModelRawIdWidget, self).__init__(attrs)

    def render(self, name, value, attrs=None):
        from django.conf import settings
        related_url = '/admin/%s/%s/' % (self.model._meta.app_label, self.model._meta.object_name.lower())
        if self.limit_choices_to:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in self.limit_choices_to.items()])
        else:
            url = ''
        if not attrs.has_key('class'):
          attrs['class'] = 'vForeignKeyRawIdAdminField' # The JavaScript looks for this hook.
        output = [super(ModelRawIdWidget, self).render(name, value, attrs)]
        # TODO: "id_" is hard-coded here. This should instead use the correct
        # API to determine the ID dynamically.
        output.append('<a href="%s%s" class="related-lookup" id="lookup_id_%s" onclick="return showRelatedObjectLookupPopup(this);"> ' % \
            (related_url, url, name))
        output.append('<img src="%simg/admin/selector-search.gif" width="16" height="16" alt="Lookup" /></a>' % settings.ADMIN_MEDIA_PREFIX)
        if value:
            output.append(self.label_for_value(value))
        return mark_safe(u''.join(output))
    
    def label_for_value(self, value):
        return '&nbsp;<strong>%s</strong>' % \
            truncate_words(self.model.objects.get(pk=value), 14)

