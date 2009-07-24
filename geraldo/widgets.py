import datetime, types, decimal
from sets import Set

from reportlab.lib.units import cm
from reportlab.lib.colors import black

from base import BAND_WIDTH, BAND_HEIGHT, Element
from utils import get_attr_value
from exceptions import AttributeNotFound

class Widget(Element):
    """A widget is a value representation on the report"""
    _height = 0 #0.5*cm
    _width = 5*cm
    style = {}
    truncate_overflow = False
    
    get_value = None # A lambda function to get customized values

    instance = None
    report = None
    generator = None
    band = None

    def __init__(self, **kwargs):
        """This initializer is prepared to set arguments informed as attribute
        values."""
        for k,v in kwargs.items():
            setattr(self, k, v)

    def clone(self):
        new = super(Widget, self).clone()
        new.style = self.style
        new.truncate_overflow = self.truncate_overflow

        new.get_value = self.get_value

        new.instance = self.instance
        new.report = self.report
        new.generator = self.generator
        new.band = self.band

        return new

class Label(Widget):
    """A label is just a simple text.
    
    'get_value' lambda must have 'text' argument."""
    _text = ''

    def _get_text(self):
        if self.get_value:
            return self.get_value(text)

        return self._text

    def _set_text(self, value):
        self._text = value

    text = property(_get_text, _set_text)

    def clone(self):
        new = super(Label, self).clone()

        if not callable(self._text):
            new._text = self._text

        return new

FIELD_ACTION_VALUE = 'value'
FIELD_ACTION_COUNT = 'count'
FIELD_ACTION_AVG = 'avg'
FIELD_ACTION_MIN = 'min'
FIELD_ACTION_MAX = 'max'
FIELD_ACTION_SUM = 'sum'
FIELD_ACTION_DISTINCT_COUNT = 'distinct_count'
FIELD_ACTION_CHOICES = {
    FIELD_ACTION_VALUE: 'Value',
    FIELD_ACTION_COUNT: 'Count',
    FIELD_ACTION_AVG: 'Avg',
    FIELD_ACTION_MIN: 'Min',
    FIELD_ACTION_MAX: 'Max',
    FIELD_ACTION_SUM: 'Sum',
    FIELD_ACTION_DISTINCT_COUNT: 'Distinct count',
}

class ObjectValue(Label):
    """This shows the value from a method, field or property from objects got
    from the queryset.
    
    You can inform an action to show the object value or an aggregation
    function on it.
    
    You can also use 'display_format' attribute to set a friendly string
    formating, with a mask or additional text.
    
    'get_value' lambda must have 'instance' argument."""
    attribute_name = None
    action = FIELD_ACTION_VALUE
    display_format = '%s'
    objects = None

    def get_object_value(self, instance=None):
        """Return the attribute value for just an object"""
        instance = instance or self.instance

        if self.get_value and instance:
            return self.get_value(instance)

        value = get_attr_value(instance, self.attribute_name)

        # For method attributes
        if type(value) == types.MethodType:
            value = value()

        return value

    def get_queryset_values(self):
        """Uses the method 'get_object_value' to get the attribute value from
        all objects in the objects list, as a list"""

        objects = self.generator.get_current_queryset()
        return map(self.get_object_value, objects)

    def _clean_empty_values(self, values):
        def _clean(val):
            if not val:
                return 0
            elif isinstance(val, decimal.Decimal):
                return float(val)
            
            return val

        return map(_clean, values)

    def action_value(self):
        return self.get_object_value()

    def action_count(self):
        values = self.get_queryset_values()
        return len([value for value in values if value])

    def action_avg(self):
        values = self.get_queryset_values()

        # Clear empty values
        values = self._clean_empty_values(values)

        return sum(values) / len(values)

    def action_min(self):
        values = self.get_queryset_values()
        return min(values)

    def action_max(self):
        values = self.get_queryset_values()
        return max(values)

    def action_sum(self):
        values = self.get_queryset_values()

        # Clear empty values
        values = self._clean_empty_values(values)

        return sum(values)

    def action_distinct_count(self):
        values = Set(self.get_queryset_values())
        return len(values)

    def _text(self):
        try: # First of all, tries to get using parent object
            value = self.band.get_object_value(obj=self)
        #except AttributeError:
        #    raise
        except AttributeNotFound:
            value = getattr(self, 'action_'+self.action)()

        text = unicode(value)
        return self.display_format%text
    text = property(lambda self: self._text())

    def clone(self):
        new = super(ObjectValue, self).clone()
        new.attribute_name = self.attribute_name
        new.action = self.action
        new.display_format = self.display_format
        new.objects = self.objects

        return new

SYSTEM_FIELD_CHOICES = {
    'report_title': 'ReportTitle',
    'page_number': 'PageNumber',
    'page_count': 'PageCount',
    'current_datetime': 'CurrentDateTime',
    'report_author': 'Author',
}

class SystemField(Label):
    """This shows system informations, like the report title, current date/time,
    page number, pages count, etc.
    
    'get_value' lambda must have 'expression' and 'fields' argument."""
    expression = '%(report_title)s'

    fields = {
            'report_title': None,
            'page_number': None,
            'page_count': None,
            'current_datetime': None,
            'report_author': None,
        }

    def __init__(self, **kwargs):
        super(SystemField, self).__init__(**kwargs)

        # This is the safe way to use the predefined fields dictionary
        self.fields = SystemField.fields.copy()

        self.fields['current_datetime'] = datetime.datetime.now()

    def text(self):
        fields = {
            'report_title': self.fields.get('report_title') or self.report.title,
            'page_number': self.fields.get('page_number') or self.generator._current_page_number + 1,
            'page_count': self.fields.get('page_count') or self.generator.get_page_count(),
            'current_datetime': self.fields.get('current_datetime') or datetime.datetime.now(),
            'report_author': self.fields.get('report_author') or self.report.author,
        }
        
        if self.get_value:
            return self.get_value(self.expression, fields)

        return self.expression%SystemFieldDict(self, fields)
    text = property(text)

    def clone(self):
        new = super(SystemField, self).clone()
        new.expression = self.expression
        new.fields = self.fields

        return new

class SystemFieldDict(dict):
    widget = None
    fields = None

    def __init__(self, widget, fields):
        self.widget = widget
        self.fields = fields or {}

    def __getitem__(self, key):
        if key.startswith('now:'):
            return self.widget.report.format_date(
                    self.fields.get('current_datetime', datetime.datetime.now()),
                    key[4:]
                    )

        return self.fields[key]

