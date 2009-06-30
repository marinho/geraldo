import datetime
from base import ReportGenerator

from geraldo.base import cm
from geraldo.utils import get_attr_value, calculate_size
from geraldo.widgets import Widget, Label, SystemField
from geraldo.graphics import Graphic, RoundRect, Rect, Line, Circle, Arc,\
        Ellipse, Image

# In development

DEFAULT_ROW_HEIGHT = 0.5*cm
DEFAULT_CHAR_WIDTH = 0.23*cm

# Default is Epson ESC/P2 standard
DEFAULT_ESCAPE_SET = {
        'line-feed': chr(10),
        'form-feed': chr(12),
        'carriage-return': chr(13),
        'condensed': chr(15),
        'cancel-condensed': chr(18),
        'line-spacing-big': chr(27)+chr(48),
        'line-spacing-normal': chr(27)+chr(49),
        'line-spacing-short': chr(27)+chr(50),
        'italic': chr(27)+chr(52),
        'cancel-italic': chr(27)+chr(53),
        }

class ReportPage(object):
    rect = None
    elements = None
    width = None

    def __init__(self):
        self.elements = []

class Paragraph(object):
    text = ''
    style = None
    height = None
    width = None

    def __init__(self, text, style=None):
        self.text = text
        self.style = style

    def wrapOn(self, page_size, width, height): # TODO
        self.height = height
        self.width = width

class TextGenerator(ReportGenerator):
    """This is a generator to output data in text/plain format.
    
    Attributes:

        * 'row_height' - should be the equivalent height of a row plus the space
          between rows. This is important to calculate how many rows has a page.
        * 'character_width' - should be the equivalent width of a character. This
          is important to calculate how many columns has a page.
        * 'to_printer' - is a boolean variable you can inform to generate a text
          to matrix printer or not. This means escape characters will be in output
          or not.
        * 'escape_set' - is a dictionary with equivalence table to escape codes.
          As far as we know, escape codes can vary depending of model or printer
          manufacturer (i.e. Epson, Lexmark, HP, etc.). This attribute is useful
          to support this. Defaul is ESC/P2 standard (Epson matrix printers)
        * 'filename' - is the file path you can inform optionally to save text to.
    """
    row_height = DEFAULT_ROW_HEIGHT
    character_width = DEFAULT_CHAR_WIDTH
    _to_printer = True
    _escape_set = DEFAULT_ESCAPE_SET

    _is_first_page = True
    _is_latest_page = True
    _current_top_position = 0
    _current_left_position = 0
    _current_page_number = 0
    _current_object = None
    _current_queryset = None
    _generation_datetime = None

    # The rendered report have pages, each page is a ReportPage instance
    _rendered_pages = None
    _page_rect = None

    def __init__(self, report, **kwargs):
        super(TextGenerator, self).__init__(report)

        # Specific attributes
        for k,v in kwargs.items():
            setattr(self, k, v)

        # Initializes some attributes
        self._rendered_pages = []
        self._groups_values = {}
        self._groups_previous_values = {}
        self._groups_changed = {}
        self._groups_stack = []

        self.update_escape_chars()

    def execute(self):
        # Initializes pages
        self._is_first_page = True

        # Render pages
        self.render_bands()

        # Generate the pages
        text = self.generate_pages()

        # Saves to file or just returns the text
        if hasattr(self, 'filename'):
            fp = file(self.filename, 'w')
            fp.write(text)
            fp.close()
        else:
            return text
 
    def render_border(self, borders_dict, rect_dict):
        """Renders a border in the coordinates setted in the rect."""
        b_all = borders_dict.get('all', None)
        if b_all:
            graphic = isinstance(b_all, Graphic) and b_all or Rect()
            graphic.set_rect(
                    left=rect_dict['left'],
                    top=rect_dict['top'] - rect_dict['height'],
                    width=rect_dict['right'] - rect_dict['left'],
                    height=rect_dict['height'],
                    )
            self._rendered_pages[-1].elements.append(graphic)

        b_left = borders_dict.get('left', None)
        if b_left:
            graphic = isinstance(b_left, Graphic) and b_left or Line()
            graphic.set_rect(
                    left=rect_dict['left'], top=rect_dict['top'],
                    right=rect_dict['left'], bottom=rect_dict['bottom']
                    )
            self._rendered_pages[-1].elements.append(graphic)

        b_top = borders_dict.get('top', None)
        if b_top:
            graphic = isinstance(b_top, Graphic) and b_top or Line()
            graphic.set_rect(
                    left=rect_dict['left'], top=rect_dict['top'],
                    right=rect_dict['right'], bottom=rect_dict['top']
                    )
            self._rendered_pages[-1].elements.append(graphic)

        b_right = borders_dict.get('right', None)
        if b_right:
            graphic = isinstance(b_right, Graphic) and b_right or Line()
            graphic.set_rect(
                    left=rect_dict['right'], top=rect_dict['top'],
                    right=rect_dict['right'], bottom=rect_dict['bottom']
                    )
            self._rendered_pages[-1].elements.append(graphic)

        b_bottom = borders_dict.get('bottom', None)
        if b_bottom:
            graphic = isinstance(b_right, Graphic) and b_right or Line()
            graphic.set_rect(
                    left=rect_dict['left'], top=rect_dict['bottom'],
                    right=rect_dict['right'], bottom=rect_dict['bottom']
                    )
            self._rendered_pages[-1].elements.append(graphic)

    def make_band_rect(self, band, top_position, left_position):
        """Returns the right band rect on the PDF canvas"""
        band_rect = {
                'left': left_position, #self.report.margin_left,
                'top': top_position,
                'right': left_position + self.calculate_size(band.width), #self.report.page_size[0] - self.report.margin_right,
                'bottom': top_position - self.calculate_size(band.height),
                'height': self.calculate_size(band.height),
                }
        return band_rect

    def render_band(self, band, top_position=None, left_position=None,
            update_top=True, current_object=None):
        """Generate a band having the current top position or informed as its
        top coordinate"""
        current_object = current_object or self._current_object

        # Page width. This should be done in a metaclass in Report domain FIXME
        self._rendered_pages[-1].width = self.calculate_size(self.report.page_size[0]) -\
                self.calculate_size(self.report.margin_left) - self.calculate_size(self.report.margin_right)

        # Default value for band width
        band.width = self.calculate_size(band.width) or self._rendered_pages[-1].width

        # Coordinates
        left_position = left_position or self.get_left_pos()

        if left_position > self.calculate_size(self.report.margin_left) and\
           getattr(band, 'display_inline', False) and\
           band.width < self.get_available_width():
            self.update_top_pos(decrease=self.calculate_size(band.height))
        else:
            self.update_left_pos(set=0)
            left_position = self.get_left_pos()

        temp_top = top_position = top_position or self.get_top_pos()

        # Calculates the band dimensions on the canvas
        band_rect = self.make_band_rect(band, top_position, left_position)

        # Band borders
        self.render_border(band.borders, band_rect)

        # Loop at band widgets
        for element in band.elements:
            # Widget element
            if isinstance(element, Widget):
                widget = element.clone()

                # Set widget colors
                widget.font_color = self.report.default_font_color

                # Set widget basic attributes
                widget.instance = current_object
                widget.generator = self
                widget.report = self.report # This should be done by a metaclass in Band domain FIXME
                widget.band = band # This should be done by a metaclass in Band domain FIXME
                widget.page = self._rendered_pages[-1]

                if isinstance(widget, SystemField):
                    widget.left = band_rect['left'] + self.calculate_size(widget.left)
                    widget.top = self.calculate_top(temp_top, self.calculate_size(widget.top))
                elif isinstance(widget, Label):
                    widget.para = self.make_paragraph(widget.text, self.make_paragraph_style(band, widget.style))

                    if widget.truncate_overflow:
                        widget.keep = KeepInFrame(
                                self.calculate_size(widget.width),
                                self.calculate_size(widget.height),
                                [widget.para],
                                mode='truncate',
                                ) # shrink
                        widget.keep.canv = self.canvas
                        widget.keep.wrap(self.calculate_size(widget.width), self.calculate_size(widget.height))

                        widget.left = band_rect['left'] + self.calculate_size(widget.left)
                        widget.top = self.calculate_top(temp_top, self.calculate_size(widget.top), self.calculate_size(widget.height))
                    else:
                        self.wrap_paragraph_on(widget.para, self.calculate_size(widget.width), self.calculate_size(widget.height))
                        widget.left = band_rect['left'] + self.calculate_size(widget.left)
                        widget.top = self.calculate_top(temp_top, self.calculate_size(widget.top), self.calculate_size(widget.para.height))

                self._rendered_pages[-1].elements.append(widget)

            # Graphic element
            elif isinstance(element, Graphic):
                graphic = element.clone()

                # Set widget basic attributes
                graphic.instance = current_object
                graphic.generator = self
                graphic.report = self.report # This should be done by a metaclass in Band domain FIXME
                graphic.band = band # This should be done by a metaclass in Band domain FIXME
                graphic.page = self._rendered_pages[-1]

                # Set graphic colors
                graphic.fill_color = graphic.fill_color or self.report.default_fill_color
                graphic.stroke_color = graphic.stroke_color or self.report.default_stroke_color

                if isinstance(graphic, RoundRect):
                    graphic.left = band_rect['left'] + self.calculate_size(graphic.left)
                    graphic.top = top_position - self.calculate_size(graphic.top) - self.calculate_size(graphic.height)
                elif isinstance(graphic, Rect):
                    graphic.left = band_rect['left'] + self.calculate_size(graphic.left)
                    graphic.top = top_position - self.calculate_size(graphic.top) - self.calculate_size(graphic.height)
                elif isinstance(graphic, Line):
                    graphic.left = band_rect['left'] + self.calculate_size(graphic.left)
                    graphic.top = top_position - self.calculate_size(graphic.top)
                    graphic.right = band_rect['left'] + self.calculate_size(graphic.right)
                    graphic.bottom = top_position - self.calculate_size(graphic.bottom)
                elif isinstance(graphic, Circle):
                    graphic.left_center = band_rect['left'] + self.calculate_size(graphic.left_center)
                    graphic.top_center = top_position - self.calculate_size(graphic.top_center)
                elif isinstance(graphic, Arc):
                    graphic.left = band_rect['left'] + self.calculate_size(graphic.left)
                    graphic.top = top_position - self.calculate_size(graphic.top)
                    graphic.right = band_rect['left'] + self.calculate_size(graphic.right)
                    graphic.bottom = top_position - self.calculate_size(graphic.bottom)
                elif isinstance(graphic, Ellipse):
                    graphic.left = band_rect['left'] + self.calculate_size(graphic.left)
                    graphic.top = top_position - self.calculate_size(graphic.top)
                    graphic.right = band_rect['left'] + self.calculate_size(graphic.right)
                    graphic.bottom = top_position - self.calculate_size(graphic.bottom)
                elif isinstance(graphic, Image):
                    graphic.left = band_rect['left'] + self.calculate_size(graphic.left)
                    graphic.top = top_position - self.calculate_size(graphic.top) - self.calculate_size(graphic.height)

                self._rendered_pages[-1].elements.append(graphic)

        # Updates top position
        if update_top:
            self.update_top_pos(self.calculate_size(band.height) + self.calculate_size(getattr(band, 'margin_top', 0)))

        # Updates left position
        if getattr(band, 'display_inline', False):
            self.update_left_pos(band.width + self.calculate_size(getattr(band, 'margin_right', 0)))
        else:
            self.update_left_pos(set=0)

        # Child bands
        for child_band in band.child_bands or []: # FIXME This "or []" here is a quickfix
            # Doesn't generate if it is not visible
            if not child_band.visible:
                continue

            self.force_blank_page_by_height(self.calculate_size(child_band.height))

            self.render_band(child_band)

    def force_blank_page_by_height(self, height):
        """Check if the height is in client available report height and
        makes a new page if necessary"""
        if self.get_available_height() < height:
            self.force_new_page()

    def force_new_page(self, insert_new_page=True):
        """Starts a new blank page"""
        # Ends the current page
        self._current_top_position = 0

        # Creates the new page
        if insert_new_page:
            self._rendered_pages.append(ReportPage())

        # Starts a new one
        self.start_new_page()

        # Page footer
        self.render_page_footer()

    def render_begin(self):
        """Renders the report begin band if it exists"""
        if not self.report.band_begin:
            return

        # Doesn't generate this band if it is not visible
        if not self.report.band_begin.visible:
            return

        # Call method that print the band area and its widgets
        self.render_band(self.report.band_begin)

    def render_summary(self):
        """Generate the report summary band if it exists"""
        if not self.report.band_summary:
            return

        # Doesn't generate this band if it is not visible
        if not self.report.band_summary.visible:
            return

        # Clears groups stack
        self._groups_stack = []

        # Check to force new page if there is no available space
        self.force_blank_page_by_height(self.calculate_size(self.report.band_summary.height))

        # Call method that print the band area and its widgets
        self.render_band(self.report.band_summary)

    def render_page_header(self):
        """Generate the report page header band if it exists"""
        if not self.report.band_page_header:
            return

        # Doesn't generate this band if it is not visible
        if not self.report.band_page_header.visible:
            return

        # Call method that print the band area and its widgets
        self.render_band(
                self.report.band_page_header,
                top_position=self.calculate_size(self.report.page_size[1]) - self.calculate_size(self.report.margin_top),
                update_top=False,
                )

    def render_page_footer(self):
        """Generate the report page footer band if it exists"""
        if not self.report.band_page_footer:
            return

        # Doesn't generate this band if it is not visible
        if not self.report.band_page_footer.visible:
            return

        # Call method that print the band area and its widgets
        self.render_band(
                self.report.band_page_footer,
                top_position=self.calculate_size(self.report.margin_bottom) +\
                    self.calculate_size(self.report.band_page_footer.height),
                update_top=False,
                )

    def render_end_current_page(self):
        """Closes the current page, using page breaker constant. Everything done after
        this will draw into a new page. Before this, using the generate_page_footer
        method to draw the footer"""

        self.render_page_footer()

        if self._is_latest_page:
            self.render_summary()

        self._current_page_number += 1
        self._is_first_page = False
        self.update_top_pos(set=0) # <---- update top position
 
    def render_bands(self):
        """Loops into the objects list to create the report pages until the end"""
        # Preparing local auxiliar variables
        self._current_page_number = 0
        self._current_object_index = 0
        objects = self.report.get_objects_list()

        # just an alias to make it easier
        d_band = self.report.band_detail

        # Empty report
        if self.report.print_if_empty and not objects:
            self.start_new_page()
            self.render_begin()
            self.render_end_current_page()

        # Loop for pages
        while self._current_object_index < len(objects):
            # Starts a new page and generates the page header band
            self.start_new_page()
            first_object_on_page = True

            # Generate the report begin band
            if self._current_page_number == 0:
                self.render_begin()

            # Does generate objects if there is no details band
            if not d_band:
                self._current_object_index = len(objects)

            # Loop for objects to go into grid on current page
            while self._current_object_index < len(objects):
                # Get current object from list
                self._current_object = objects[self._current_object_index]

                # Renders group bands for changed values
                self.calc_changed_groups(first_object_on_page)

                if not first_object_on_page:
                    self.render_groups_footers()

                self.render_groups_headers()

                # Generate this band only if it is visible
                if d_band.visible:
                    self.render_band(d_band)

                # Renders subreports
                self.render_subreports()

                # Next object
                self._current_object_index += 1
                first_object_on_page = False

                # Break this if this page doesn't suppport nothing more...
                # ... if there is no more available height
                if self.get_available_height() < self.calculate_size(d_band.height):
                    # right margin is not considered to calculate the necessary space
                    d_width = self.calculate_size(d_band.width) + self.calculate_size(getattr(d_band, 'margin_left', 0))

                    # ... and this is not an inline displayed detail band or there is no width available
                    if not getattr(d_band, 'display_inline', False) or self.get_available_width() < d_width:
                        break

                # ... or this band forces a new page and this is not the last object in objects list
                elif d_band.force_new_page and self._current_object_index < len(objects):
                    break

            # Sets this is the latest page or not
            self._is_latest_page = self._current_object_index >= len(objects)

            # Renders the finish group footer bands
            if self._is_latest_page:
                self.calc_changed_groups(False)
                self.render_groups_footers(force=True)

            # Ends the current page, printing footer and summary and necessary
            self.render_end_current_page()

            # Breaks if this is the latest item
            if self._is_latest_page:
                break

            # Increment page number
            self._current_page_number += 1

    def start_new_page(self, with_header=True):
        """Do everything necessary to be done to start a new page"""
        self._rendered_pages.append(ReportPage())

        if with_header:
            self.render_page_header()

        # Page borders
        if self.report.borders:
            if not self._page_rect:
                self._page_rect = self.report.get_page_rect()
                self._page_rect['top'] = self.calculate_size(self.report.page_size[1]) - self._page_rect['top']
                self._page_rect['bottom'] = self.calculate_size(self.report.page_size[1]) - self._page_rect['bottom']

            self.render_border(self.report.borders, self._page_rect)

    def calculate_size(self, size):
        """Uses the function 'calculate_size' to calculate a size"""
        if isinstance(size, basestring):
            if size.endswith('*cols'):
                return int(size.split('*')[0]) * self.character_width
            elif size.endswith('*rows'):
                return int(size.split('*')[0]) * self.row_height
        
        return calculate_size(size)

    def calculate_top(self, *args):
        return sum(args)

    def get_left_pos(self):
        """Returns the left position of the drawer. Is useful on inline displayed detail bands"""
        return self.calculate_size(self.report.margin_left) + self._current_left_position

    def get_available_width(self):
        return self.calculate_size(self.report.page_size[0]) - self.calculate_size(self.report.margin_left) -\
                self.calculate_size(self.report.margin_right) - self._current_left_position

    def get_top_pos(self):
        """Since the coordinates are bottom-left on PDF, we have to use this to get
        the current top position, considering also the top margin."""
        ret = self.calculate_size(self.report.margin_top) + self._current_top_position

        if self.report.band_page_header:
            ret += self.calculate_size(self.report.band_page_header.height)

        return ret

    def get_available_height(self):
        """Returns the available client height area from the current top position
        until the end of page, considering the bottom margin."""
        ret = self.calculate_size(self.report.page_size[1]) - self.calculate_size(self.report.margin_bottom) -\
                self.calculate_size(self.report.margin_top) - self._current_top_position

        if self.report.band_page_header:
            ret -= self.calculate_size(self.report.band_page_header.height)

        if self.report.band_page_footer:
            ret -= self.calculate_size(self.report.band_page_footer.height)

        return ret

    def update_top_pos(self, increase=0, decrease=0, set=None):
        """Updates the current top position controller, increasing (by default),
        decreasing or setting it with a new value."""
        if set is not None:
            self._current_top_position = set
        else:        
            self._current_top_position += increase
            self._current_top_position -= decrease

        return self._current_top_position

    def update_left_pos(self, increase=0, decrease=0, set=None):
        """Updates the current left position controller, increasing (by default),
        decreasing or setting it with a new value."""
        if set is not None:
            self._current_left_position = set
        else:        
            self._current_left_position += increase
            self._current_left_position -= decrease

        return self._current_left_position

    def get_page_count(self):
        """Calculate and returns the page count for this report. The challenge
        here is do this calculate before to generate the pages."""
        return len(self._rendered_pages)

    def make_paragraph(self, text, style=None): # XXX
        """Uses the Paragraph class to return a new paragraph object"""
        return Paragraph(text, style)

    def wrap_paragraph_on(self, paragraph, width, height): # XXX
        """Wraps the paragraph on the height/width informed"""
        paragraph.wrapOn(self.report.page_size, width, height)

    # Stylizing

    def set_fill_color(self, color):
        """Sets the current fill on canvas. Used for fonts and shape fills"""
        pass
    
    def set_stroke_color(self, color):
        """Sets the current stroke on canvas"""
        pass

    def set_stroke_width(self, width):
        """Sets the stroke/line width for shapes"""
        pass

    # Groups topic

    def calc_changed_groups(self, force_no_changed=False):
        """Defines which groups has been changed their driver values to be
        used to render group bands"""
        changed = force_no_changed

        # Stores the previous group values
        self._groups_previous_values = self._groups_values.copy()

        # Loops on groups until find the first changed, then all under it are considered
        # changed also
        for group in self.report.groups:
            # Gets the current value to compare with the old one
            current_value = get_attr_value(self._current_object, group.attribute_name)

            # Set changed as True if if wasn't and there is a change
            changed = changed or current_value != self._groups_values.get(group, None)

            # Stores new values
            self._groups_changed[group] = changed
            self._groups_values[group] = current_value

            # Appends to the stack
            if changed:
                self._groups_stack.append(group)

    def render_groups_headers(self):
        """Renders the report headers using 'changed' definition calculated by
        'calc_changed_groups'"""

        # Loops on groups to render changed ones
        for group in self.report.groups:
            if self._groups_changed.get(group, None) and group.band_header:
                self.force_blank_page_by_height(self.calculate_size(group.band_header.height))
                self.render_band(group.band_header)

    def render_groups_footers(self, force=False):
        """Renders the report footers using previous 'changed' definition calculated by
        'calc_changed_groups'"""

        reversed_groups = [group for group in self.report.groups]
        reversed_groups.reverse()

        # Loops on groups to render changed ones
        for group in reversed_groups:
            if force or ( self._groups_changed.get(group, None) and\
                          self._groups_stack and\
                          self._groups_stack[-1] == group ):
                #if not force and (not self._groups_stack or self._groups_stack[-1] != group):
                #    continue
                
                if group.band_footer:
                    self.force_blank_page_by_height(self.calculate_size(group.band_footer.height))
                    self.render_band(group.band_footer)

                self._groups_stack.pop()

    def get_current_queryset(self):
        """Returns the current queryset. This solves a problem with subreports
        footers and headers, and solves also flexibility and customization issues."""

        # Customized and SubReports
        if self._current_queryset is not None:
            return self._current_queryset

        # Groups
        elif self._groups_stack:
            return self.get_objects_in_group()

        # Defaul detail driver queryset
        return self.report.queryset

    def get_objects_in_group(self):
        """Returns objects filtered in the current group or all if there is no
        group"""

        filter = dict([(group.attribute_name, self._groups_previous_values.get(group, None))\
                for group in self.report.groups if group in self._groups_stack])

        def filter_object(obj):
            for k,v in filter.items():
                if get_attr_value(obj, k) != v:
                    return False

            return obj

        return [obj for obj in self.report.queryset if filter_object(obj)]

    # SubReports

    def render_subreports(self):
        """Renders subreports bands for the current object in, usings its
        own queryset.
        
        For a while just the detail band is rendered. Maybe in future we
        change this to accept header and footer."""

        def force_new_page(height):
            # Forces new page if there is no available space
            if self.get_available_height() < self.calculate_size(height):
                self.render_page_footer()
                self.force_new_page(insert_new_page=False)

        for subreport in self.report.subreports:
            # Subreports must have detail band
            if not subreport.band_detail:
                continue

            # Sets the parent object and automatically clear the queryset
            # in memory
            subreport.parent_object = self._current_object

            # Sets the temporary currenty queryset
            self._current_queryset = subreport.get_objects_list()

            # Loops objects
            for num, obj in enumerate(subreport.get_objects_list()):
                # Renders the header band
                if num == 0 and subreport.band_header:
                    # Forces new page if there is no available space
                    force_new_page(subreport.band_header.height)

                    # Renders the header band
                    self.render_band(subreport.band_header)

                # Forces new page if there is no available space
                force_new_page(subreport.band_detail.height)

                # Renders the detail band
                self.render_band(subreport.band_detail, current_object=obj)

            # Renders the footer band
            if subreport.band_footer:
                # Forces new page if there is no available space
                force_new_page(subreport.band_footer.height)

                # Renders the header band
                self.render_band(subreport.band_footer)

            # Sets back the default currenty queryset
            self._current_queryset = None

    def make_paragraph_style(self, band, style=None):
        """Merge report default_style + band default_style + widget style"""
        d_style = self.report.default_style.copy()

        if band.default_style:
            for k,v in band.default_style.items():
                d_style[k] = v

        if style:
            for k,v in style.items():
                d_style[k] = v

        import datetime

        return dict(name=datetime.datetime.now().strftime('%H%m%s'), **d_style)

    # METHODS THAT ARE TOTALLY SPECIFIC TO THIS GENERATOR AND MUST
    # OVERRIDE THE SUPERCLASS EQUIVALENT ONES

    def generate_pages(self):
        """Specific method that generates the pages"""
        self._generation_datetime = datetime.datetime.now()
        self._output = u''

        # Escapes
        self.add_escapes_report_start();

        for num, page in enumerate([page for page in self._rendered_pages if page.elements]):
            # Escapes
            self.add_escapes_page_start(num);

            _page_output = [u' ' * self.page_columns_count] * self.page_rows_count

            self._current_page_number = num

            # Loop at band widgets
            for element in page.elements:
                # Widget element
                if isinstance(element, Widget):
                    widget = element
                    self.generate_widget(widget, _page_output, num)

            # Adds the page output to output string
            self._output += u'\n'.join(_page_output)

            # Escapes
            self.add_escapes_page_end(num);

        # Escapes
        self.add_escapes_report_end();

        return self._output

    def generate_widget(self, widget, page_output, page_number=0):
        """Renders a widget element on canvas"""
        self.print_in_page_output(page_output, widget.text, widget.rect)

    def generate_graphic(self, graphic, page_output): # TODO
        """Renders a graphic element"""
        pass

    def print_in_page_output(self, page_output, text, rect): # XXX
        """Changes the array page_output (a matrix with rows and cols equivalent
        to rows and cols in a matrix printer page) inserting the text value in
        the left/top coordinates."""

        # Make the real rect for this text
        text_rect = {
            'top': int(round(self.calculate_size(rect['top']) / self.row_height)),
            'left': int(round(self.calculate_size(rect['left']) / self.character_width)),
            'height': int(round(self.calculate_size(rect['height']) / self.row_height)),
            'width': int(round(self.calculate_size(rect['width']) / self.character_width)),
            'bottom': int(round(self.calculate_size(rect['bottom']) / self.row_height)),
            'right': int(round(self.calculate_size(rect['right']) / self.character_width)),
            }

        if text_rect['height'] and text_rect['width']:
            # Make a text with the exact width
            text = text.ljust(text_rect['width'])[:text_rect['width']] # Align to left - TODO: should have center and right justifying also

            # Inserts the text into the page output buffer
            _temp = page_output[text_rect['top']]
            _temp = _temp[:text_rect['left']] + text + _temp[text_rect['right']:]
            page_output[text_rect['top']] = _temp[:self.get_page_columns_count()]

    def add_escapes_report_start(self):
        """Adds the escape commands to the output variable"""
        self._output += self.escapes_report_start

    def add_escapes_report_end(self):
        """Adds the escape commands to the output variable"""
        self._output += self.escapes_report_end

    def add_escapes_page_start(self, num):
        """Adds the escape commands to the output variable"""
        self._output += self.escapes_page_start

    def add_escapes_page_end(self, num):
        """Adds the escape commands to the output variable"""
        self._output += self.escapes_page_end

    def update_escape_chars(self):
        """Sets the escape chars to be ran for some events on report generation"""
        if self.to_printer:
            self.escapes_report_start = ''
            self.escapes_report_end = ''
            self.escapes_page_start = ''
            self.escapes_page_end = self.escape_set['form-feed']
        else:
            self.escapes_report_start = ''
            self.escapes_report_end = ''
            self.escapes_page_start = ''
            self.escapes_page_end = ''

    def get_escape_set(self):
        return self._escape_set

    def set_escape_set(self, val):
        self._escape_set = val
        self.update_escape_chars()

    escape_set = property(get_escape_set, set_escape_set)

    def get_to_printer(self):
        return self._to_printer

    def set_to_printer(self, val):
        self.to_printer = val
        self.update_escape_chars()

    to_printer = property(get_to_printer, set_to_printer)

    def get_page_rows_count(self):
        return int(round(self.calculate_size(self.report.page_size[1]) / self.row_height))
    page_rows_count = property(get_page_rows_count)

    def get_page_columns_count(self):
        return int(round(self.calculate_size(self.report.page_size[0]) / self.character_width))
    page_columns_count = property(get_page_columns_count)

