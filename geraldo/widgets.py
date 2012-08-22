import datetime, types, decimal, re

try: 
    set 
except NameError: 
    from sets import Set as set     # Python 2.3 fallback 

from base import BAND_WIDTH, BAND_HEIGHT, Element, SubReport
from utils import get_attr_value, SYSTEM_FIELD_CHOICES, FIELD_ACTION_VALUE, FIELD_ACTION_COUNT,\
        FIELD_ACTION_AVG, FIELD_ACTION_MIN, FIELD_ACTION_MAX, FIELD_ACTION_SUM,\
        FIELD_ACTION_DISTINCT_COUNT, cm, black
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
    borders = None

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
        new.borders = self.borders

        return new

class Label(Widget):
    """A label is just a simple text.
    
    'get_value' lambda must have 'text' argument."""
    _text = ''

    _repr_for_cache_attrs = ('text','left','top','height','width','style','visible')

    def _get_text(self):
        if self.get_value:
            try:
                return self.get_value(self, self._text)
            except TypeError:
                return self.get_value(self._text)

        return self._text

    def _set_text(self, value):
        self._text = value

    text = property(_get_text, _set_text)

    def clone(self):
        new = super(Label, self).clone()

        if not callable(self._text):
            new._text = self._text

        return new

EXP_QUOTED = re.compile('\w\(([^\'"].+?[^\'"])(|,.*?)\)')
EXP_QUOTED_SUB = re.compile('\(([^\'"].+?[^\'"])(|,.*?)\)')
EXP_TOKENS = re.compile('([\w\._]+|\*\*|\+|\-|\*|\/)')

class ObjectValue(Label):
    """This shows the value from a method, field or property from objects got
    from the queryset.
    
    You can inform an action to show the object value or an aggregation
    function on it.
    
    You can also use 'display_format' attribute to set a friendly string
    formating, with a mask or additional text.
    
    'get_value' and 'get_text' lambda attributes must have 'instance' argument.
    
    Set 'stores_text_in_cache' to False if you want this widget get its value
    and text on render and generate moments."""

    attribute_name = None
    action = FIELD_ACTION_VALUE
    display_format = '%s'
    objects = None
    get_text = None # A lambda function to get customized display values
    stores_text_in_cache = True
    expression = None
    converts_decimal_to_float = False
    converts_float_to_decimal = True
    _cached_text = None
    on_expression_error = None # Expected arguments:
                               #  - widget
                               #  - instance
                               #  - exception
                               #  - expression

    def __init__(self, *args, **kwargs):
        super(ObjectValue, self).__init__(*args, **kwargs)

        if self.expression:
            self.prepare_expression()

    def prepare_expression(self):
        if not self.expression:
            pass

        self.expression = self.expression.replace(' ','')

        while True:
            f = EXP_QUOTED.findall(self.expression)
            if not f:
                # Replace simple attribute name or method to value("")
                if '(' not in self.expression:
                    self.expression = 'value("%s")' % self.expression
                break

            self.expression = EXP_QUOTED_SUB.sub('("%s"%s)'%(f[0][0], f[0][1]), self.expression, 1)

    def get_object_value(self, instance=None, attribute_name=None):
        """Return the attribute value for just an object"""
        instance = instance or self.instance
        attribute_name = attribute_name or self.attribute_name

        # Checks lambda and instance
        if self.get_value and instance:
            try:
                return self.get_value(self, instance)
            except TypeError:
                return self.get_value(instance)

        # Checks this is an expression
        tokens = EXP_TOKENS.split(attribute_name)
        tokens = filter(bool, tokens) # Cleans empty parts
        if len(tokens) > 1:
            values = {}
            for token in tokens:
                if not token in ('+','-','*','/','**') and not  token.isdigit():
                    values[token] = self.get_object_value(instance, token)
            return eval(attribute_name, values)

        # Gets value with function
        value = get_attr_value(instance, attribute_name)

        # For method attributes --- FIXME: check what does this code here, because
        #                           get_attr_value has a code to do that, using
        #                           callable() checking
        if type(value) == types.MethodType:
            value = value()

        return value

    def get_queryset_values(self, attribute_name=None):
        """Uses the method 'get_object_value' to get the attribute value from
        all objects in the objects list, as a list"""

        objects = self.generator.get_current_queryset()
        return map(lambda obj: self.get_object_value(obj, attribute_name), objects)

    def _clean_empty_values(self, values):
        def clean(val):
            if not val:
                return 0
            elif isinstance(val, decimal.Decimal) and self.converts_decimal_to_float:
                return float(val)
            elif isinstance(val, float) and self.converts_float_to_decimal:
                return decimal.Decimal(str(val))
            
            return val

        return map(clean, values)

    def action_value(self, attribute_name=None):
        return self.get_object_value(attribute_name=attribute_name)

    def action_count(self, attribute_name=None):
        # Returns the total count of objects with valid values on informed attribute
        values = self.get_queryset_values(attribute_name)
        return len(filter(lambda v: v is not None, values))

    def action_avg(self, attribute_name=None):
        values = self.get_queryset_values(attribute_name)

        # Clear empty values
        values = self._clean_empty_values(values)

        return sum(values) / len(values)

    def action_min(self, attribute_name=None):
        values = self.get_queryset_values(attribute_name)
        return min(values)

    def action_max(self, attribute_name=None):
        values = self.get_queryset_values(attribute_name)
        return max(values)

    def action_sum(self, attribute_name=None):
        values = self.get_queryset_values(attribute_name)

        # Clear empty values
        values = self._clean_empty_values(values)

        return sum(values)

    def action_distinct_count(self, attribute_name=None):
        values = filter(lambda v: v is not None, self.get_queryset_values(attribute_name))
        return len(set(values))

    def action_coalesce(self, attribute_name=None, default=''):
        value = self.get_object_value(attribute_name=attribute_name)
        return value or unicode(default)

    def _text(self):
        if not self.stores_text_in_cache or self._cached_text is None:
            try: # Before all, tries to get the value using parent object
                value = self.band.get_object_value(obj=self)
            except AttributeNotFound:
                if self.expression:
                    value = self.get_value_by_expression()
                else:
                    value = getattr(self, 'action_'+self.action)()

            if self.get_text:
                try:
                    self._cached_text = unicode(self.get_text(self, self.instance, value))
                except TypeError:
                    self._cached_text = unicode(self.get_text(self.instance, value))
            else:
                self._cached_text = unicode(value)
            
        return self.display_format % self._cached_text

    def _set_text(self, value):
        self._cached_text = value

    text = property(lambda self: self._text(), _set_text)

    def clone(self):
        new = super(ObjectValue, self).clone()
        new.attribute_name = self.attribute_name
        new.action = self.action
        new.display_format = self.display_format
        new.objects = self.objects
        new.stores_text_in_cache = self.stores_text_in_cache
        new.expression = self.expression
        new.on_expression_error = self.on_expression_error

        return new

    def get_value_by_expression(self, expression=None):
        """Parses a given expression to get complex calculated values"""

        expression = expression or self.expression

        if not self.instance:
            global_vars = {}
        elif isinstance(self.instance, dict):
            global_vars = self.instance.copy()
        else:
            global_vars = self.instance.__dict__.copy()

        global_vars.update({
            'value': self.action_value,
            'count': self.action_count,
            'avg': self.action_avg,
            'min': self.action_min,
            'max': self.action_max,
            'sum': self.action_sum,
            'distinct_count': self.action_distinct_count,
            'coalesce': self.action_coalesce,
            })

        if isinstance(self.report, SubReport):
            global_vars.update({
                'parent': self.report.parent_object,
                'p': self.report.parent_object, # Just a short alias
                })

        try:
            return eval(expression, global_vars)
        except Exception, e:
            if not callable(self.on_expression_error):
                raise

            return self.on_expression_error(self, e, expression, self.instance)

class SystemField(Label):
    """This shows system informations, like the report title, current date/time,
    page number, pages count, etc.
    
    'get_value' lambda must have 'expression' and 'fields' argument."""
    expression = '%(report_title)s'

    fields = {
            'report_title': None,
            'page_number': None,
            'first_page_number': None,
            'last_page_number': None,
            'page_count': None,
            'current_datetime': None,
            'report_author': None,
        }

    def __init__(self, **kwargs):
        super(SystemField, self).__init__(**kwargs)

        # This is the safe way to use the predefined fields dictionary
        self.fields = SystemField.fields.copy()

        self.fields['current_datetime'] = datetime.datetime.now()

    def _text(self):
        page_number = (self.fields.get('page_number') or self.generator._current_page_number) + self.generator.first_page_number - 1
        page_count = self.fields.get('page_count') or self.generator.get_page_count()

        fields = {
            'report_title': self.fields.get('report_title') or self.report.title,
            'page_number': page_number,
            'first_page_number': self.generator.first_page_number,
            'last_page_number': page_count + self.generator.first_page_number - 1,
            'page_count': page_count,
            'current_datetime': self.fields.get('current_datetime') or datetime.datetime.now(),
            'report_author': self.fields.get('report_author') or self.report.author,
        }
        
        if self.get_value:
            return self.get_value(self.expression, fields)

        return self.expression%SystemFieldDict(self, fields)

    def text(self): return self._text()
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

        super(SystemFieldDict, self).__init__(**fields)

    def __getitem__(self, key):
        if key.startswith('now:'):
            return self.widget.report.format_date(
                    self.fields.get('current_datetime', datetime.datetime.now()),
                    key[4:]
                    )

        elif key.startswith('var:'):
            return self.widget.report.get_variable_value(name=key[4:], system_fields=self)

        return self.fields[key]

