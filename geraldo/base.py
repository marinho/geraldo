import copy, types, new

try: 
    set 
except NameError: 
    from sets import Set as set     # Python 2.3 fallback 

from utils import calculate_size, get_attr_value, landscape, format_date, memoize,\
        BAND_WIDTH, BAND_HEIGHT, CROSS_COLS, CROSS_ROWS, cm, A4, black, TA_LEFT, TA_CENTER,\
        TA_RIGHT
from exceptions import EmptyQueryset, ObjectNotFound, ManyObjectsFound,\
        AttributeNotFound, NotYetImplemented
from cache import DEFAULT_CACHE_STATUS, CACHE_BACKEND, CACHE_FILE_ROOT

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

    def destroy(self):
        try:
            children = self.get_children()
        except (NotYetImplemented, AttributeError):
            children = None

        # Destroy children
        if children:
            for ch in children:
                try:
                    ch.destroy()
                except AttributeError:
                    pass

        del children
        del self

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

            found.extend(ch_found)

        # Cleans using a set
        found = list(set(found))

        # Found nothing
        if not found:
            raise ObjectNotFound('There is no child with name "%s"'%name)
        
        # Found many
        elif len(found) > 1 and not many:
            raise ManyObjectsFound('There are many childs with name "%s"'%name)

        return many and found or found[0]

    def find_by_type(self, typ):
        """Find child by informed type (and raises an exception if doesn't
        find).
        
        Attributes:
            
            * typ - class type to find
        """
        found = []

        # Get object children
        children = self.get_children()

        for child in children:
            # Child with the type it is searching for
            if isinstance(child, typ):
                found.append(child)

            # Search on child's children
            try:
                ch_found = child.find_by_type(typ)
            except ObjectNotFound:
                ch_found = []

            found.extend(ch_found)

        # Cleans using a set
        found = list(set(found))

        return found

    def get_children(self):
        """Returns all children elements from this one. This must be overriden
        by inherited class."""
        raise NotYetImplemented()

    def remove_from_parent(self):
        """Remove this object from its parent one"""
        if not self.parent:
            raise Exception('This object has no parent')

        self.parent.remove_child(self)

    def remove_child(self, obj):
        """Removes a child from this one. This must be overriden by inherited
        class."""
        raise NotYetImplemented()

    def set_parent_on_children(self):
        """Goes on every child and set their attribute 'parent' for this one.
        This must be overriden by inherited class."""
        raise NotYetImplemented()

    def get_object_value(self, obj=None, attribute_name=None, action=None):
        """Override this method to customize the behaviour of object getting its value."""
        try:
            return self.parent.get_object_value(obj, attribute_name, action)
        except AttributeError:
            raise AttributeNotFound()

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
    
    # Events (don't make a method with their names, override 'do_*' instead)
    before_print = None         # |     before render
    before_generate = None      # |     after render / before generate
    after_print = None          # V     after generate
    on_new_page = None

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

        return list(self.queryset)

    def format_date(self, date, expression):
        """Use a date format string method to return formatted datetime.

        You should override this method to force UTF-8 decode or something like
        this (until we find a better and agnosthic solution).
        
        Please don't hack this method up. Just override it on your report class."""

        return format_date(date, expression)

    def get_children(self):
        ret = []

        # Bands
        ret.extend(filter(bool, [
            self.band_begin,
            self.band_summary,
            self.band_page_header,
            self.band_page_footer,
            self.band_detail
        ]))

        # Groups
        if isinstance(self.groups, (list, tuple)):
            ret.extend(self.groups)

        # Borders
        if isinstance(self.borders, dict):
            ret.extend(filter(lambda e: isinstance(e, Element),self.borders.values()))

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

    # Events methods
    def do_before_print(self, generator):
        if self.before_print:
            self.before_print(self, generator)

    def do_before_generate(self, generator):
        if self.before_generate:
            self.before_generate(self, generator)

    def do_after_print(self, generator):
        if self.after_print:
            self.after_print(self, generator)

    def do_on_new_page(self, page, page_number, generator):
        if self.on_new_page:
            self.on_new_page(self, page, page_number, generator)

    def get_variable_value(self, name, system_fields):
        """Returns the value for a given variable name"""
        return system_fields.widget.generator.variables[name]


# Useful to find declared report classes without manual registration
_registered_report_classes = []

class ReportMetaclass(type):
    """This metaclass registers the declared classes to a local variable."""
    
    def __new__(cls, name, bases, attrs):
        # Merges default_style with inherited report classes
        if isinstance(attrs.get('default_style', None), dict):
            default_style = {}

            for base in bases:
                if isinstance(getattr(base, 'default_style', None), dict):
                    default_style.update(base.default_style)

            default_style.update(attrs['default_style'])
            attrs['default_style'] = default_style

        new_class = super(ReportMetaclass, cls).__new__(cls, name, bases, attrs)

        # Defines a registration ID
        if attrs.get('_registered_id', None) is None:
            new_class._registered_id = '%s.%s'%(new_class.__module__, name)

        # Appends the new class to list of registered report classes
        if new_class._registered_id != 'geraldo.base.Report':
            _registered_report_classes.append(new_class)

        return new_class

@memoize
def get_report_class_by_registered_id(reg_id):
    for report_class in _registered_report_classes:
        if getattr(report_class, '_registered_id', None) == reg_id:
            return report_class

    return None

class Report(BaseReport):
    """This class must be inherited to be used as a new report.
    
    A report has bands and is driven by a QuerySet. It can have a title and
    margins definitions.
    
    Depends on ReportLab to work properly"""

    __metaclass__ = ReportMetaclass

    # Report properties
    title = ''
    author = ''
    subject = '' # Can be used also as the report description
    keywords = ''

    # Page dimensions
    first_page_number = 1
    page_size = A4
    margin_top = 1*cm
    margin_bottom = 1*cm
    margin_left = 1*cm
    margin_right = 1*cm
    _page_rect = None

    # SubReports
    subreports = None

    # Look and feel
    additional_fonts = None
    default_style = None

    # Caching related attributes
    cache_status = None
    cache_backend = None
    cache_prefix = None
    cache_file_root = None

    def __init__(self, queryset=None):
        super(Report, self).__init__(queryset)

        # Default attributes
        self.subreports = self.subreports and list(self.subreports) or []
        self.default_style = self.default_style or {}
        self.additional_fonts = self.additional_fonts or {}

        # Caching related attributes
        if self.cache_status is None:
            self.cache_status = DEFAULT_CACHE_STATUS
        if self.cache_backend is None:
            self.cache_backend = CACHE_BACKEND
        if self.cache_prefix is None:
            self.cache_prefix = '-'.join([self.__class__.__module__, self.__class__.__name__])
        if self.cache_file_root is None:
            self.cache_file_root = CACHE_FILE_ROOT

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

    def generate_under_process_by(self, generator_class, *args, **kwargs):
        """Uses the power of multiprocessing library to run report generation under
        a Process and save memory consumming, with better use of multi-core servers.
        
        This just will work well if you are generating in a destination file or
        file-like object (i.e. an HttpResponse on Django).
        
        It doesn't returns nothing because Process doesn't."""

        import tempfile, random, os
        from utils import run_under_process

        # Checks 'filename' argument
        if 'filename' in kwargs and not isinstance(kwargs['filename'], basestring):
            # Stores file-like object
            filelike = kwargs.pop('filename')

            # Make a randomic temporary filename
            chars = map(chr, range(ord('a'), ord('z')) + range(ord('0'), ord('9')))
            filename = ''.join([random.choice(chars) for c in range(40)])
            kwargs['filename'] = os.path.join(tempfile.gettempdir(), filename)
        else:
            filelike = None

        @run_under_process
        def generate_report(report, generator_class, *args, **kwargs):
            # Generate report into response object
            report.generate_by(generator_class, *args, **kwargs)

        # Run report generation
        generate_report(self, generator_class, *args, **kwargs)

        # Loads temp file
        if filelike:
            # Reads the temp file
            fp = file(kwargs['filename'])
            cont = fp.read()
            fp.close()

            # Writes temp file content in file-like object
            filelike.write(cont)

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
            ret.extend(self.subreports)

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
    
    - 'queryset_string' must be a string with path for Python compatible queryset.
    - 'get_queryset' is an optional lambda attribute can be used in replacement to
      queryset_string to make more dynamic querysets
    
    Examples:
    
        * '%(object)s.user_permissions.all()'
        * '%(object)s.groups.all()'
        * 'Message.objects.filter(user=%(object)s)'
        * 'Message.objects.filter(user__id=%(object)s.id)'"""

    _queryset_string = None
    _parent_object = None
    _queryset = None

    band_detail = None
    band_header = None
    band_footer = None

    visible = True

    get_queryset = None # This must be a lambda function

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
        if not self._queryset:
            # Lambda function
            if self.get_queryset:
                self._queryset = self.get_queryset(self, self.parent_object)

            # Queryset string
            elif self.parent_object and self.queryset_string:
                # Replaces the string representer to a local variable identifier
                queryset_string = self.queryset_string%{
                    'object': 'parent_object',  # TODO: Remove in future
                    'parent': 'parent_object',
                    'p': 'parent_object', # Just a short alias
                    }

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
        ret.extend(filter(bool, [
            self.band_detail,
            self.band_header,
            self.band_footer,
            ]))

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
    borders = {'top': None, 'right': None, 'bottom': None, 'left': None, 'all': None}
    elements = None
    child_bands = None
    force_new_page = False
    default_style = None
    auto_expand_height = False
    is_detail = False
    
    # Events (don't make a method with their names, override 'do_*' instead)
    before_print = None
    after_print = None

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
        ret.extend(self.elements)
        ret.extend(self.child_bands)

        # Borders
        if isinstance(self.borders, dict):
            ret.extend(filter(lambda e: isinstance(e, Element),self.borders.values()))

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

    # Events methods
    def do_before_print(self, generator):
        if self.before_print:
            self.before_print(self, generator)

    def do_after_print(self, generator):
        if self.after_print:
            self.after_print(self, generator)

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
    force_new_page = False

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
    
    # Events (don't make a method with their names, override 'do_*' instead)
    before_print = None
    after_print = None

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

        # Copy events
        new.before_print = self.before_print
        new.after_print = self.after_print

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

    # Events methods
    def do_before_print(self, generator):
        if self.before_print:
            self.before_print(self, generator)

    def do_after_print(self, generator):
        if self.after_print:
            self.after_print(self, generator)

    _repr_for_cache_attrs = ('left','top','height','width','visible')
    def repr_for_cache_hash_key(self):
        return unicode(dict([(attr, getattr(self, attr)) for attr in self._repr_for_cache_attrs]))

class ManyElements(GeraldoObject):
    """Class that makes the objects creation more dynamic."""

    element_class = None
    count = None
    start_left = None
    start_top = None
    visible = True
    element_kwargs = None

    def __init__(self, element_class, count, start_left=None, start_top=None,
            visible=None, **kwargs):

        self.element_class = element_class
        self.count = count
        self.start_left = start_left is not None and start_left or self.start_left
        self.start_top = start_top is not None and start_top or self.start_top
        self.visible = visible is not None and visible or self.visible

        # Stores the additinal arguments to use when creating the elements
        self.element_kwargs = kwargs.copy()

    def get_elements(self, cross_cols=None):
        """Returns the elements (or create them if they don't exist."""

        from cross_reference import CrossReferenceMatrix

        count = self.count

        # Get cross cols
        if not cross_cols and isinstance(self.report.queryset, CrossReferenceMatrix):
            cross_cols = self.report.queryset.cols()

            if count == CROSS_COLS:
                count = len(cross_cols)

        _elements = []

        # Loop for count of elements to be created
        next_left = self.start_left
        next_top = self.start_top
        for num in range(count):
            kwargs = self.element_kwargs.copy()

            # Set attributes before creation
            for k,v in kwargs.items():
                if v == CROSS_COLS:
                    try:
                        kwargs[k] = cross_cols[num]
                    except IndexError:
                        kwargs[k] = cross_cols[-1]
                elif isinstance(v, (list,tuple)) and v:
                    try:
                        kwargs[k] = v[num]
                    except IndexError:
                        kwargs[k] = v[-1]

            # Create the element
            el = self.element_class(**kwargs)

            # Set attributes after creation
            if self.start_left is not None: # Maybe we should support distance here
                el.left = next_left
                next_left += el.width

            if self.start_top is not None: # Maybe we should support distance here
                el.top = next_top
                next_top += el.height

            _elements.append(el)

        return _elements

