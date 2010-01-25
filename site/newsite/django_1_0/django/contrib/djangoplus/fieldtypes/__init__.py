import datetime
from django.db import models
from django.db.models import signals
from django.conf import settings
from django.utils import simplejson as json
from django.dispatch import dispatcher

"""
JSONField: http://www.djangosnippets.org/snippets/377/
"""

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, datetime.time):
            return obj.strftime('%H:%M:%S')
        return json.JSONEncoder.default(self, obj)
        
def dumps(data):
    return JSONEncoder().encode(data)
    
def loads(str):
    return json.loads(str, encoding=settings.DEFAULT_CHARSET)
    
class JSONField(models.TextField):
    def db_type(self):
        return 'text'
        
    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        return dumps(value)
    
    def contribute_to_class(self, cls, name):
        super(JSONField, self).contribute_to_class(cls, name)
        dispatcher.connect(self.post_init, signal=signals.post_init, sender=cls)
        
        def get_json(model_instance):
            return dumps(getattr(model_instance, self.attname, None))
        setattr(cls, 'get_%s_json' % self.name, get_json)
    
        def set_json(model_instance, json):
            return setattr(model_instance, self.attname, loads(json))
        setattr(cls, 'set_%s_json' % self.name, set_json)
    
    def post_init(self, instance=None):
        value = self.value_from_object(instance)
        if (value):
            setattr(instance, self.attname, loads(value))
        else:
            setattr(instance, self.attname, None)

