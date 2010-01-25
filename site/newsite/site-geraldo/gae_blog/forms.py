from google.appengine.ext import db

from django import forms

from models import Entry
from migration import import_from_json

BLOG_FORMAT_CHOICES = (
    ('html','html'),
    ('rest','rest'),
    ('markdown','markdown'),
    ('text','text'),
)

class FormEntry(forms.ModelForm):
    class Meta:
        model = Entry
        exclude = ('pub_date','author','tags','sequence',)

    tags_string = forms.Field(required=False, label='Tags')

    def __init__(self, *args, **kwargs):
        self.base_fields['format'].widget = forms.Select(
                choices=BLOG_FORMAT_CHOICES
                )

        super(FormEntry, self).__init__(*args, **kwargs)

        if self.instance:
            self.fields['tags_string'].initial = ' '.join(self.instance.tags)

    def clean_tags_string(self):
        if not self.cleaned_data['tags_string']:
            return []

        return [db.Category(tag) for tag in self.cleaned_data['tags_string'].split(' ')]

    def save(self, *args, **kwargs):
        entry = super(FormEntry, self).save(*args, **kwargs)
        entry.tags = self.cleaned_data['tags_string']
        entry.save()

        return entry

class FormImport(forms.Form):
    file = forms.FileField()

    def do_import(self):
        data = self.cleaned_data['file'].read()
        return import_from_json(data)

