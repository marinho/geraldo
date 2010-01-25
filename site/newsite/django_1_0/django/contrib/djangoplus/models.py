from django.db import models
from django import template
from django.template.defaultfilters import slugify

class DynamicTemplate(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, unique=True)
    group = models.SlugField(blank=True)
    content = models.TextField()

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('title',)

    def render(self, context):
        return template.Template(self.content).render(template.Context(context))

# SIGNALS AND LISTENERS
from django.db.models import signals
from django.dispatch import dispatcher

# DynamicTemplate
def dynamictemplate_pre_save(sender, instance, signal, *args, **kwargs):
    # Cria slug
    instance.slug = slugify(instance.title)
    instance.group = slugify(instance.group)

dispatcher.connect(dynamictemplate_pre_save, signal=signals.pre_save, sender=DynamicTemplate)

