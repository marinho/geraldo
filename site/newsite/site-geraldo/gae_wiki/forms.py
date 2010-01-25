from django import forms

from google.appengine.ext import db

from models import Wiki

WIKI_FORMAT_CHOICES = (
    ('html','html'),
    ('rest','rest'),
    ('markdown','markdown'),
    ('text','text'),
)

class FormWiki(forms.ModelForm):
    class Meta:
        model = Wiki
        exclude = ('pub_date','author','sequence','old_id','tags',)

    temp_tags = forms.Field(required=False, label='Tags')

    def __init__(self, *args, **kwargs):
        self.base_fields['format'].widget = forms.Select(choices=WIKI_FORMAT_CHOICES)

        super(FormWiki, self).__init__(*args, **kwargs)

        if self.instance:
            self.fields['temp_tags'].initial = ' '.join(self.instance.tags)

    def save(self, commit=True):
        if self.instance:
            wiki = self.instance
        else:
            wiki = Wiki()

        wiki.title = self.cleaned_data['title']
        wiki.slug = self.cleaned_data['slug']
        wiki.description = self.cleaned_data['description']
        wiki.text = self.cleaned_data['text']
        wiki.format = self.cleaned_data['format']
        wiki.published = self.cleaned_data['published']
        wiki.template = self.cleaned_data['template']
        wiki.show_in_rss = self.cleaned_data['show_in_rss']
        wiki.cacheable = self.cleaned_data['cacheable']
        wiki.show_in_rss = self.cleaned_data['show_in_rss']
        wiki.disable_comments = self.cleaned_data['disable_comments']

        if self.cleaned_data['temp_tags']:
            wiki.tags = map(lambda tag: db.Category(tag), self.cleaned_data['temp_tags'].split(' '))
        else:
            wiki.tags = []

        if commit:
            wiki.save()

        return wiki
