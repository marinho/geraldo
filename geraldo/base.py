import copy, types

from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black

REPORT_PAGE_BREAK = 'report-page-break'

def get_attr_value(obj, attr):
    """This function returns a value from a object doesn't matters if the
    attribute is a function or not"""
    value = getattr(obj, attr)
    
    if type(value) == types.MethodType:
        return value()

    return value

class BaseReport(object):
    """This class must be inherited to be used as a new report.
    
    A report has bands and is driven by a QuerySet. It can have a title and
    margins definitions.
    
    Depends on ReportLab to work properly"""

    # Bands - is not possible to have more than one band from the same kind
    band_begin = None
    band_summary = None
    band_page_header = None
    band_page_footer = None
    band_detail = None
    groups = None

    # Data source driver
    queryset = None
    print_if_empty = False # This means if a queryset is empty, the report will
                           # be generated or not

    # Colors
    default_font_color = black
    default_stroke_color = black
    default_fill_color = black

    def __init__(self, queryset=None):
        self.queryset = queryset or self.queryset
        self.groups = self.groups or []

    def get_objects_list(self):
        """Returns the list with objects to be rendered.
        
        This should be refactored in the future to support big amounts of
        records."""
        if not self.queryset:
            return []

        return [object for object in self.queryset]

class Report(BaseReport):
    """Class to be inherited and used to make reports"""
    # Report properties
    title = ''
    author = ''
    
    # Page dimensions
    page_size = A4
    margin_top = 1*cm
    margin_bottom = 1*cm
    margin_left = 1*cm
    margin_right = 1*cm

    def generate_by(self, generator_class, *args, **kwargs):
        """This method uses a generator inherited class to generate a report
        to a desired format, like XML, HTML or PDF, for example.
        
        The arguments *args and **kwargs are passed to class initializer."""
        generator = generator_class(self, *args, **kwargs)

        return generator.execute()

class SubReport(BaseReport):
    """Class to be used for subreport objects. It doesn't need to be inherited"""
    queryset_string = None

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

class ReportBand(object):
    """A band is a horizontal area in the report. It can be used to print
    things on the top, on summary, on page header, on page footer or one time
    per object from queryset."""
    height = 1*cm
    visible = True
    borders = {'top': None, 'right': None, 'bottom': None, 'left': None,
            'all': None}
    elements = None
    child_bands = None
    force_new_page = False

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

        self.elements = self.elements or []
        self.child_bands = self.child_bands or []

    def clone(self):
        """Does a deep copy of this band to be rendered"""
        return copy.deepcopy(self)

class TableBand(ReportBand): # TODO
    """This band must be used only as a detail band. It doesn't is repeated per
    object, but instead of it is streched and have its rows increased."""
    pass

class ReportGroup(object):
    """This a report grouper class. A report can be multiple groupped by
    attribute values.
    
    Yet in development process."""
    attribute_name = None
    band_header = None
    band_footer = None

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

