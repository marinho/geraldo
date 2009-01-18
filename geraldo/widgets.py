import datetime, types
from sets import Set

from reportlab.lib.units import cm
from reportlab.lib.colors import black

BAND_WIDTH = 'band-width'

class Widget(object):
    """A widget is a value representation on the report"""
    height = 0.5*cm
    _width = 5*cm
    left = 0
    top = 0
    visible = True
    style = {}
    
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

    # 'width' property
    def _get_width(self):
        if self._width == BAND_WIDTH and self.band:
            return self.band.width

        return self._width

    def _set_width(self, value):
        self._width = value

    width = property(_get_width, _set_width)

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

    def get_object_value(self, instance=None):
        """Return the attribute value for just an object"""
        instance = instance or self.instance

        if self.get_value and instance:
            return self.get_value(instance)

        value = getattr(instance, self.attribute_name)

        # For method attributes
        if type(value) == types.MethodType:
            value = value()

        return value

    def get_queryset_values(self):
        """Uses the method 'get_object_value' to get the attribute value from
        all objects in the report queryset, as a list"""
        return [self.get_object_value(instance) for instance in self.report.queryset]

    def action_value(self):
        return self.get_object_value()

    def action_count(self):
        values = self.get_queryset_values()
        return len([value for value in values if value])

    def action_avg(self):
        values = self.get_queryset_values()
        return sum(values) / len(values)

    def action_min(self):
        values = self.get_queryset_values()
        return min(values)

    def action_max(self):
        values = self.get_queryset_values()
        return max(values)

    def action_sum(self):
        values = self.get_queryset_values()
        return sum(values)

    def action_distinct_count(self):
        values = Set(self.get_queryset_values())
        return len(values)

    @property
    def text(self):
        text = unicode(getattr(self, 'action_'+self.action)())
        return self.display_format%text

SYSTEM_REPORT_TITLE = 1
SYSTEM_PAGE_NUMBER = 2
SYSTEM_PAGE_COUNT = 3
SYSTEM_CURRENT_DATETIME = 4
SYSTEM_REPORT_AUTHOR = 5
SYSTEM_FIELD_CHOICES = {
    SYSTEM_REPORT_TITLE: 'ReportTitle',
    SYSTEM_PAGE_NUMBER: 'PageNumber',
    SYSTEM_PAGE_COUNT: 'PageCount',
    SYSTEM_CURRENT_DATETIME: 'CurrentDateTime',
    SYSTEM_REPORT_AUTHOR: 'Author',
}

class SystemField(Label):
    """This shows system informations, like the report title, current date/time,
    page number, pages count, etc.
    
    'get_value' lambda must have 'kind' and 'fields' argument."""
    kind = SYSTEM_REPORT_TITLE

    @property
    def text(self):
        fields =  {
            SYSTEM_REPORT_TITLE: self.report.title,
            SYSTEM_PAGE_NUMBER: self.generator._current_page_number,
            SYSTEM_PAGE_COUNT: self.generator.get_page_count(),
            SYSTEM_CURRENT_DATETIME: datetime.datetime.now(),
            SYSTEM_REPORT_AUTHOR: self.report.author,
        }
        
        if self.get_value:
            return self.get_value(self.kind, fields)

        return fields[self.kind]

