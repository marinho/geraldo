class Widget(object):
    """A widget is a value representation on the report"""
    height = None
    width = None
    left = 0
    top = 0
    visible = True
    style = {}

    def get_value(self):
        """Used to returns the value that will show on the report"""
        pass

    def __init__(self, **kwargs):
        """This initializer is prepared to set arguments informed as attribute
        values."""
        for k,v in kwargs.items():
            setattr(self, k, v)

class Label(Widget):
    """A label is just a simple text"""
    text = ''

class ObjectValue(Label):
    """This shows the value from a method, field or property from objects got
    from the queryset"""
    attribute_name = None
    instance = None

    @property
    def text(self):
        return unicode(getattr(self.instance, self.attribute_name))

SYSTEM_REPORT_TITLE = 1
SYSTEM_PAGE_NUMBER = 2
SYSTEM_PAGE_COUNT = 3
SYSTEM_CURRENT_DATETIME = 4
SYSTEM_FIELD_CHOICES = {
    SYSTEM_REPORT_TITLE: 'ReportTitle',
    SYSTEM_PAGE_NUMBER: 'PageNumber',
    SYSTEM_PAGE_COUNT: 'PageCount',
    SYSTEM_CURRENT_DATETIME: 'CurrentDateTime',
}

class SystemField(Label):
    """This shows system informations, like the report title, current date/time,
    page number, pages count, etc."""
    kind = SYSTEM_REPORT_TITLE

