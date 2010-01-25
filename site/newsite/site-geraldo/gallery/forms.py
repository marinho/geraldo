from google.appengine.ext import db

from django import forms

from models import Item

class FormItem(forms.ModelForm):
    class Meta:
        model = Item
        exclude = ('pub_date','thumb','mimetype','file','tags',)

    file_to_upload = forms.Field(widget=forms.FileInput, required=False)
    tags_string = forms.Field(required=False, label='Tags')

    def __init__(self, *args, **kwargs):
        super(FormItem, self).__init__(*args, **kwargs)

        if self.instance:
            self.fields['tags_string'].initial = ' '.join(self.instance.tags)

    def clean_tags_string(self):
        if not self.cleaned_data['tags_string']:
            return []

        return [db.Category(tag) for tag in self.cleaned_data['tags_string'].split(' ')]

    def save(self, *args, **kwargs):
        img = super(FormItem, self).save(*args, **kwargs)
        img.tags = self.cleaned_data['tags_string']
        img.save()

        return img

