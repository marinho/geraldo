import copy, types, sets

from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from utils import calculate_size, get_attr_value
from exceptions import EmptyQueryset, ObjectNotFound, ManyObjectsFound,\
        AttributeNotFound

BAND_WIDTH = 'band-width'
BAND_HEIGHT = 'band-height'

def landscape(page_size):
    return page_size[1], page_size[0]

class GeraldoObject(object):
    """Base class inherited by all report classes, including band, subreports,
    groups, graphics and widgets.
    
    Attributes:
        
        * parent - this is setted by its parent when it is initializing. There
          is no automated way to get it."""

    parent = None

    def __init__(self, *kwargs):
        if 'name' in kwargs:
            self.name = kwargs.pop('name')

    def find_by_name(self, name, many=False):
        """Find child by informed name (and raises an exception if doesn't
        find).
        
        Attributes:
            
            * name - object name to find
            * many - boolean attribute that means it returns many objects
              or not - in the case there are more than one object with the
              same name
        """
        found = []

        # Get object children
        children = self.get_children()

        for child in children:
            # Child with the name it is searching for
            if getattr(child, 'name', None) == name:
                found.append(child)

            # Search on child's children
            try:
                ch_found = child.find_by_name(name, many=True)
            except ObjectNotFound:
                ch_found = []

            found += ch_found

        # Cleans using a set
        found = list(sets.Set(found))

        # Found nothing
        if not found:
            raise ObjectNotFound('There is no child with name "%s"'%name)
        
        # Found many
        elif len(found) > 1 and not many:
            raise ManyObjectsFound('There are many childs with name "%s"'%name)

        return many and found or found[0]

    def get_children(self):
        """Returns all children elements from this one. This must be overriden
        by inherited class."""
        raise Exception('Not yet implemented!')

    def remove_from_parent(self):
        """Remove this object from its parent one"""
        if not self.parent:
            raise Exception('This object has no parent')

        self.parent.remove_child(self)

    def remove_child(self, obj):
        """Removes a child from this one. This must be overriden by inherited
        class."""
        raise Exception('Not yet implemented!')

    def set_parent_on_children(self):
        """Goes on every child and set their attribute 'parent' for this one.
        This must be overriden by inherited class."""
        raise Exception('Not yet implemented!')

    def get_object_value(self, obj=None, attribute_name=None, action=None):
        """Override this method to customize the behaviour of object getting
        its value."""
        return self.parent.get_object_value(obj, attribute_name, action)

class BaseReport(GeraldoObject):
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

        # Calls the method that set this as parent if their children
        self.set_parent_on_children()

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
            self.band_detail.is_detail = True

        # Groups
        groups = self.groups
        self.groups = [isinstance(group, ReportGroup) and group or group() for group in groups]

    def get_objects_list(self):
        """Returns the list with objects to be rendered.
        
        This should be refactored in the future to support big amounts of
        objects."""
        if not self.queryset:
            return []

        return [object for object in self.queryset]

    def format_date(self, date, expression):
        """Use a date format string method to return formatted datetime.

        You should override this method to force UTF-8 decode or something like
        this (until we find a better and agnosthic solution).
        
        Please don't hack this method up. Just override it on your report class."""
        return date.strftime(expression)

    def get_children(self):
        ret = []

        # Bands
        ret += filter(bool, [
            self.band_begin,
            self.band_summary,
            self.band_page_header,
            self.band_page_footer,
            self.band_detail
        ])

        # Groups
        if isinstance(self.groups, (list, tuple)):
            ret += self.groups

        # Borders
        if isinstance(self.borders, dict):
            ret += filter(lambda e: isinstance(e, Element),self.borders.values())

        return ret

    def remove_child(self, obj):
        # Bands
        if obj == self.band_begin: self.band_begin = None
        if obj == self.band_summary: self.band_summary = None
        if obj == self.band_page_header: self.band_page_header = None
        if obj == self.band_page_footer: self.band_page_footer = None
        if obj == self.band_detail: self.band_detail = None

        # Groups
        if isinstance(self.groups, (list, tuple)) and obj in self.groups:
            self.groups.remove(obj)

        # Borders
        if isinstance(self.borders, dict) and obj in self.borders.values():
            for k,v in self.borders.items():
                if v == obj:
                    self.borders.pop(k)

    def set_parent_on_children(self):
        # Bands
        if self.band_begin: self.band_begin.parent = self
        if self.band_summary: self.band_summary.parent = self
        if self.band_page_header: self.band_page_header.parent = self
        if self.band_page_footer: self.band_page_footer.parent = self
        if self.band_detail: self.band_detail.parent = self

        # Groups
        if isinstance(self.groups, (list, tuple)):
            for group in self.groups:
                group.parent = self

        # Borders
        if isinstance(self.borders, dict):
            for v in self.borders.values():
                if isinstance(v, GeraldoObject):
                    v.parent = self

    def get_object_value(self, obj=None, attribute_name=None, action=None):
        """Just raises an exception to force object to get its value
        by itself. This is the end point for this method calling
        ( because it is called from children and the children are
        called from their children and on..."""
        raise AttributeNotFound

class Report(BaseReport):
    """This class must be inherited to be used as a new report.
    
    A report has bands and is driven by a QuerySet. It can have a title and
    margins definitions.
    
    Depends on ReportLab to work properly"""

    # Report properties
    title = ''
    author = ''
    subject = '' # Can be used also as the report description
    keywords = ''

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

        # Calls the method that set this as parent if their children
        self.set_parent_on_children()

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
            client_width = calculate_size(self.page_size[0]) - calculate_size(self.margin_left) - calculate_size(self.margin_right)
            client_height = calculate_size(self.page_size[1]) - calculate_size(self.margin_top) - calculate_size(self.margin_bottom)

            self._page_rect = {
                'left': calculate_size(self.margin_left),
                'top': calculate_size(self.margin_top),
                'right': calculate_size(self.page_size[0]) - calculate_size(self.margin_right),
                'bottom': calculate_size(self.page_size[1]) - calculate_size(self.margin_bottom),
                'width': client_width,
                'height': client_height,
                }

        return self._page_rect

    def get_children(self):
        ret = super(Report, self).get_children()

        if isinstance(self.subreports, (list, tuple)):
            ret += self.subreports

        return ret

    def remove_child(self, obj):
        super(Report, self).remove_child(obj)

        # Subreports
        if isinstance(self.subreports, (list, tuple)) and obj in self.subreports:
            self.subreports.remove(obj)

    def set_parent_on_children(self):
        super(Report, self).set_parent_on_children()

        # Subreports
        if isinstance(self.subreports, (list, tuple)):
            for subreport in self.subreports:
                subreport.parent = self

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

    visible = True

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            # Validates backward incompatibility for 'detail_band'
            if k == 'detail_band':
                k = 'band_detail'

                import warnings
                warnings.warn("Attribute 'detail_band' in SubReport class is deprecated. Use 'band_detail' as well.")

            setattr(self, k, v)

        # Calls the method that set this as parent if their children
        self.set_parent_on_children()

        # Sets detail band
        if self.band_detail:
            self.band_detail.is_detail = True

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
    queryset = property(queryset)

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

    def get_children(self):
        ret = super(SubReport, self).get_children()
        ret += filter(bool, [
            self.band_detail,
            self.band_header,
            self.band_footer,
            ])

        return ret

    def remove_child(self, obj):
        super(SubReport, self).remove_child(obj)

        # Bands
        if obj == self.band_detail: self.band_detail = None
        if obj == self.band_header: self.band_header = None
        if obj == self.band_footer: self.band_footer = None

    def set_parent_on_children(self):
        super(SubReport, self).set_parent_on_children()

        # Bands
        if self.band_detail: self.band_detail.parent = self
        if self.band_header: self.band_header.parent = self
        if self.band_footer: self.band_footer.parent = self

class ReportBand(GeraldoObject):
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
    auto_expand_height = False
    is_detail = False

    def __init__(self, **kwargs):
        for k,v in kwargs.items():
            setattr(self, k, v)

        # Default values for elements, child bands and default style lists
        self.elements = self.elements and list(self.elements) or []
        self.child_bands = self.child_bands and list(self.child_bands) or []
        self.default_style = self.default_style or {}

        # Transforms band classes to band objects
        self.transform_classes_to_objects()

        # Calls the method that set this as parent if their children
        self.set_parent_on_children()

    def transform_classes_to_objects(self):
        """Finds all child band classes in this class and instantiante them. This
        is important to have a safety on separe inherited reports each one
        from other."""
        
        child_bands = self.child_bands
        self.child_bands = [isinstance(child, ReportBand) and child or child()
                for child in child_bands]

    def get_children(self):
        ret = []
        ret += self.elements
        ret += self.child_bands

        # Borders
        if isinstance(self.borders, dict):
            ret += filter(lambda e: isinstance(e, Element),self.borders.values())

        return ret

    def remove_child(self, obj):
        # Elements
        if isinstance(self.elements, (list, tuple)) and obj in self.elements:
            self.elements.remove(obj)

        # Child bands
        if isinstance(self.child_bands, (list, tuple)) and obj in self.child_bands:
            self.child_bands.remove(obj)

        # Borders
        if isinstance(self.borders, dict) and obj in self.borders.values():
            for k,v in self.borders.items():
                if v == obj:
                    self.borders.pop(k)

    def set_parent_on_children(self):
        # Elements
        if isinstance(self.elements, (list, tuple)):
            for element in self.elements:
                element.parent = self

        # Child bands
        if isinstance(self.child_bands, (list, tuple)):
            for child_band in self.child_bands:
                child_band.parent = self

        # Borders
        if isinstance(self.borders, dict):
            for v in self.borders.values():
                if isinstance(v, GeraldoObject):
                    v.parent = self

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

class ReportGroup(GeraldoObject):
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

        # Calls the method that set this as parent if their children
        self.set_parent_on_children()

    def transform_classes_to_objects(self):
        """Finds all band classes in this class and instantiante them. This
        is important to have a safety on separe inherited reports each one
        from other."""
        
        if self.band_header and not isinstance(self.band_header, ReportBand):
            self.band_header = self.band_header()
        
        if self.band_footer and not isinstance(self.band_footer, ReportBand):
            self.band_footer = self.band_footer()

    def get_children(self):
        return filter(bool, [
            self.band_header,
            self.band_footer,
            ])

    def remove_child(self, obj):
        # Bands
        if obj == self.band_header: self.band_header = None
        if obj == self.band_footer: self.band_footer = None

    def set_parent_on_children(self):
        # Bands
        if self.band_header: self.band_header.parent = self
        if self.band_footer: self.band_footer.parent = self
    
class Element(GeraldoObject):
    """The base class for widgets and graphics"""
    left = 0
    top = 0
    _width = 0
    _height = 0
    visible = True

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
        """Returns a copy of this element"""
        #return copy.deepcopy(self)
        new = self.__class__()
        new.left = self.left
        new.top = self.top
        new._width = self._width
        new._height = self._height
        new.visible = self.visible

        if hasattr(self, 'name'):
            new.name = self.name

        return new

    def get_rect(self, force=False):
        """Returns a dictionary with positions and dimensions of this element"""
        if not force:
            try:
                return self._rect
            except AttributeError:
                pass

        self._rect = {
                'top': self.top,
                'left': self.left,
                'height': self.height,
                'width': self.width,
                }

        try:
            self._rect['right'] = self.right
        except AttributeError:
            self._rect['right'] = self.generator.calculate_size(self._rect['left']) +\
                    self.generator.calculate_size(self._rect['width'])

        try:
            self._rect['bottom'] = self.bottom
        except AttributeError:
            self._rect['bottom'] = self.generator.calculate_size(self._rect['top']) +\
                    self.generator.calculate_size(self._rect['height'])

        return self._rect
    rect = property(get_rect)

    def get_children(self):
        return []

    def set_parent_on_children(self):
        pass

