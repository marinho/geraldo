import copy, types

from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black

BAND_WIDTH = 'band-width'
BAND_HEIGHT = 'band-height'

def landscape(page_size):
    return page_size[1], page_size[0]

class BaseReport(object):
    """Basic Report class, inherited and used to make reports adn subreports"""

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

    # Style and colors
    default_font_color = black
    default_stroke_color = black
    default_fill_color = black
    borders = None

    def __init__(self, queryset=None):
        self.queryset = queryset or self.queryset

        if self.queryset is None:
            self.queryset = []

        self.groups = self.groups and list(self.groups) or []

        # Transforms band classes to band objects
        self.transform_classes_to_objects()

    def transform_classes_to_objects(self):
        """Finds all band classes in the report and instantiante them. This
        is important to have a safety on separe inherited reports each one
        from other."""

        # Basic bands
        if self.band_begin and not isinstance(self.band_begin, ReportBand):
            self.band_begin = self.band_begin()

        if self.band_summary and not isinstance(self.band_summary, ReportBand):
            self.band_summary = self.band_summary()

        if self.band_page_header and not isinstance(self.band_page_header, ReportBand):
            self.band_page_header = self.band_page_header()

        if self.band_page_footer and not isinstance(self.band_page_footer, ReportBand):
            self.band_page_footer = self.band_page_footer()

        if self.band_detail and not isinstance(self.band_detail, ReportBand):
            self.band_detail = self.band_detail()

        # Groups
        groups = self.groups
        self.groups = [isinstance(group, ReportGroup) and group or group() for group in groups]

    def get_objects_list(self):
        """Returns the list with objects to be rendered.
        
        This should be refactored in the future to support big amounts of
        records."""
        if not self.queryset:
            return []

        return [object for object in self.queryset]

    def format_date(self, date, expression):
        """Use a date format string method to return formatted datetime"""
        return date.strftime(expression)

class EmptyQueryset(Exception):
    pass

class Report(BaseReport):
    """This class must be inherited to be used as a new report.
    
    A report has bands and is driven by a QuerySet. It can have a title and
    margins definitions.
    
    Depends on ReportLab to work properly"""
    # Report properties
    title = ''
    author = ''
    
    # Page dimensions
    page_size = A4
    margin_top = 1*cm
    margin_bottom = 1*cm
    margin_left = 1*cm
    margin_right = 1*cm
    _page_rect = None

    # SubReports
    subreports = None

    default_style = None

    def __init__(self, queryset=None):
        super(Report, self).__init__(queryset)

        self.subreports = self.subreports and list(self.subreports) or []
        self.default_style = self.default_style or {}

    def generate_by(self, generator_class, *args, **kwargs):
        """This method uses a generator inherited class to generate a report
        to a desired format, like XML, HTML or PDF, for example.
        
        The arguments *args and **kwargs are passed to class initializer."""

        # Check empty queryset and raises an error if this is not acceptable
        if not self.print_if_empty and not self.queryset:
            raise EmptyQueryset("This report doesn't accept empty queryset")

        # Initialize generator instance
        generator = generator_class(self, *args, **kwargs)

        return generator.execute()

    def get_page_rect(self):
        """Calculates a dictionary with page dimensions inside the margins
        and returns. It is used to make page borders."""
        if not self._page_rect:
            client_width = self.page_size[0] - self.margin_left - self.margin_right
            client_height = self.page_size[1] - self.margin_top - self.margin_bottom

            self._page_rect = {
                'left': self.margin_left,
                'top': self.margin_top,
                'right': self.page_size[0] - self.margin_right,
                'bottom': self.page_size[1] - self.margin_bottom,
                'width': client_width,
                'height': client_height,
                }

        return self._page_rect


class SubReport(BaseReport):
    """Class to be used for subreport objects. It doesn't need to be inherited.
    
    'queryset_string' must be a string with path for Python compatible queryset.
    
    Examples:
    
        * '%(object)s.user_permissions.all()'
        * '%(object)s.groups.all()'
        * 'Message.objects.filter(user=%(object)s)'
        * 'Message.objects.filter(user__id=%(object)s.id)'
    """
    _queryset_string = None
    _parent_object = None
    _queryset = None

    band_detail = None
    band_header = None
    band_footer = None

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            # Validates backward incompatibility for 'detail_band'
            if k == 'detail_band':
                k = 'band_detail'

                import warnings
                warnings.warn("Attribute 'detail_band' in SubReport class is deprecated. Use 'band_detail' as well.")

            setattr(self, k, v)

    @property
    def queryset(self):
        if not self._queryset and self.parent_object and self.queryset_string:
            # Replaces the string representer to a local variable identifier
            queryset_string = self.queryset_string%{'object': 'parent_object'}

            # Loads the queryset from string
            self._queryset = eval(
                    queryset_string,
                    {'parent_object': self.parent_object},
                    )

        return self._queryset

    def _get_parent_object(self):
        return self._parent_object

    def _set_parent_object(self, value):
        # Clears queryset
        self._queryset = None
        self._parent_object = value

    parent_object = property(_get_parent_object, _set_parent_object)

    def _get_queryset_string(self):
        return self._queryset_string

    def _set_queryset_string(self, value):
        # Clears queryset
        self._queryset = None
        self._queryset_string = value

    queryset_string = property(_get_queryset_string, _set_queryset_string)

class ReportBand(object):
    """A band is a horizontal area in the report. It can be used to print
    things on the top, on summary, on page header, on page footer or one time
    per object from queryset."""
    height = 1*cm
    width = None # Useful only on detail bands
    visible = True
    borders = {'top': None, 'right': None, 'bottom': None, 'left': None,
            'all': None}
    elements = None
    child_bands = None
    force_new_page = False
    default_style = None

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

        # Default values for elements, child bands and default style lists
        self.elements = self.elements and list(self.elements) or []
        self.child_bands = self.child_bands and list(self.child_bands) or []
        self.default_style = self.default_style or {}

        # Transforms band classes to band objects
        self.transform_classes_to_objects()

    def clone(self):
        """Does a deep copy of this band to be rendered"""
        return copy.deepcopy(self)

    def transform_classes_to_objects(self):
        """Finds all child band classes in this class and instantiante them. This
        is important to have a safety on separe inherited reports each one
        from other."""
        
        child_bands = self.child_bands
        self.child_bands = [isinstance(child, ReportBand) and child or child()
                for child in child_bands]

class DetailBand(ReportBand):
    """You should use this class instead of ReportBand in detail bands.
    
    It is useful when you want to have detail band with strict width, with
    margins or displayed inline like labels.
    
     * display_inline: use it together attribute 'width' to specify that you
       want to make many detail bands per line. Useful to make labels."""

    margin_top = 0
    margin_bottom = 0
    margin_left = 0
    margin_right = 0

    # With this attribute as True, the band will try to align in the same line
    display_inline = False

class TableBand(ReportBand): # TODO
    """This band must be used only as a detail band. It doesn't is repeated per
    object, but instead of it is streched and have its rows increased."""
    pass

class ReportGroup(object):
    """This a report grouper class. A report can be multiple groupped by
    attribute values."""
    attribute_name = None
    band_header = None
    band_footer = None

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

        # Transforms band classes to band objects
        self.transform_classes_to_objects()

    def transform_classes_to_objects(self):
        """Finds all band classes in this class and instantiante them. This
        is important to have a safety on separe inherited reports each one
        from other."""
        
        if self.band_header and not isinstance(self.band_header, ReportBand):
            self.band_header = self.band_header()
        
        if self.band_footer and not isinstance(self.band_footer, ReportBand):
            self.band_footer = self.band_footer()

class Element(object):
    """The base class for widgets and graphics"""
    left = 0
    top = 0
    _width = 0
    _height = 0

    # 'width' property
    def _get_width(self):
        if self._width == BAND_WIDTH and self.band:
            return self.band.width

        return self._width

    def _set_width(self, value):
        self._width = value

    width = property(_get_width, _set_width)

    # 'height' property
    def _get_height(self):
        if self._height == BAND_HEIGHT and self.band:
            return self.band.height

        return self._height

    def _set_height(self, value):
        self._height = value

    height = property(_get_height, _set_height)

    def clone(self):
        """Uses deepcopy to return a copy of this element"""
        return copy.deepcopy(self)

