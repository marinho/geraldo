# Admin registrations
from django.contrib import admin
from django.contrib.admin.options import ModelAdmin

from models import DynamicTemplate

class DynamicTemplateAdmin(ModelAdmin):
    list_display = ('title','slug','group',)
    search_fields = ('title','content','group')


admin.site.register(DynamicTemplate, DynamicTemplateAdmin)

