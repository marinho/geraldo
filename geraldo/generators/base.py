from geraldo.utils import get_attr_value, calculate_size
from geraldo.widgets import Widget, Label, SystemField
from geraldo.graphics import Graphic, RoundRect, Rect, Line, Circle, Arc,\
        Ellipse, Image

class ReportPage(object):
    rect = None
    elements = None
    width = None

    def __init__(self):
        self.elements = []

class ReportGenerator(object):
    """A report generator is used to generate a report to a specific format."""

    _is_first_page = True
    _is_latest_page = True
    _current_top_position = 0
    _current_left_position = 0
    _current_page_number = 0
    _current_object = None
    _current_queryset = None
    _generation_datetime = None

    # Groupping
    _groups_values = None
    _groups_working_values = None
    _groups_changed = None
    _groups_stack = None

    # The rendered report has pages, each page is a ReportPage instance
    _rendered_pages = None
    _page_rect = None

    def __init__(self, report):
        """This method should be overrided to receive others arguments"""
        self.report = report

        # Initializes some attributes
        self._rendered_pages = []
        self._groups_values = {}
        self._groups_working_values = {}
        self._groups_changed = {}
        self._groups_stack = []

    def execute(self):
        """This method must be overrided to execute the report generation."""

        # Initializes pages
        self._is_first_page = True
 
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

        # Sets the current object
        current_object = current_object or self._current_object

        # Page width. This should be done in a metaclass in Report domain TODO
        self._rendered_pages[-1].width = self.calculate_size(self.report.page_size[0]) -\
                self.calculate_size(self.report.margin_left) - self.calculate_size(self.report.margin_right)

        # Default value for band width
        band.width = self.calculate_size(band.width) or self._rendered_pages[-1].width

        # Coordinates
        left_position = left_position or self.get_left_pos()

        # Increases the top position when being an inline displayed detail band
        if left_position > self.calculate_size(self.report.margin_left) and\
           getattr(band, 'display_inline', False) and\
           band.width < self.get_available_width():
            temp_height = band.height + getattr(band, 'margin_top', 0) + getattr(band, 'margin_bottom', 0)
            self.update_top_pos(decrease=self.calculate_size(temp_height))
        else:
            self.update_left_pos(set=0)
            left_position = self.get_left_pos()

        temp_top = top_position = top_position or self.get_top_pos()

        # Calculates the band dimensions on the canvas
        band_rect = self.make_band_rect(band, top_position, left_position)

        # Band borders
        self.render_border(band.borders, band_rect)

        # Variable that stores the highest height at all elements
        highest_height = 0

        # Loop at band widgets
        for element in band.elements:
            # Doesn't render not visible element
            if not element.visible:
                continue

            # Widget element
            if isinstance(element, Widget):
                widget = element.clone()

                # Set widget colors
                widget.font_color = self.report.default_font_color

                # Set widget basic attributes
                widget.instance = current_object
                widget.generator = self
                widget.report = self.report # This should be done by a metaclass in Band domain TODO
                widget.band = band # This should be done by a metaclass in Band domain TODO
                widget.page = self._rendered_pages[-1]

                if isinstance(widget, SystemField):
                    widget.left = band_rect['left'] + self.calculate_size(widget.left)
                    widget.top = self.calculate_top(temp_top, self.calculate_size(widget.top))

                    temp_height = self.calculate_size(element.top) + self.calculate_size(widget.height)
                elif isinstance(widget, Label):
                    widget.para = self.make_paragraph(widget.text, self.make_paragraph_style(band, widget.style))

                    if widget.truncate_overflow:
                        self.keep_in_frame(
                                widget,
                                self.calculate_size(widget.width),
                                self.calculate_size(widget.height),
                                [widget.para],
                                mode='truncate',
                                )

                        widget.left = band_rect['left'] + self.calculate_size(widget.left)
                        widget.top = self.calculate_top(temp_top, self.calculate_size(widget.top), self.calculate_size(widget.height))
                    else:
                        self.wrap_paragraph_on(widget.para, self.calculate_size(widget.width), self.calculate_size(widget.height))
                        widget.left = band_rect['left'] + self.calculate_size(widget.left)
                        widget.top = self.calculate_top(temp_top, self.calculate_size(widget.top), self.calculate_size(widget.para.height))

                    temp_height = self.calculate_size(element.top) + self.calculate_size(widget.para.height)
                else:
                    temp_height = self.calculate_size(element.top) + self.calculate_size(widget.height)

                # Sets element height as the highest
                if temp_height > highest_height:
                    highest_height = temp_height

                self._rendered_pages[-1].elements.append(widget)

            # Graphic element
            elif isinstance(element, Graphic):
                graphic = element.clone()

                # Set widget basic attributes
                graphic.instance = current_object
                graphic.generator = self
                graphic.report = self.report # This should be done by a metaclass in Band domain TODO
                graphic.band = band # This should be done by a metaclass in Band domain TODO
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

                # Sets element height as the highest
                temp_height = self.calculate_size(element.top) + self.calculate_size(graphic.height)
                if temp_height > highest_height:
                    highest_height = temp_height

                self._rendered_pages[-1].elements.append(graphic)

        # Updates top position
        if update_top:
            if band.auto_expand_height:
                band_height = highest_height
            else:
                band_height = self.calculate_size(band.height)

            band_height += self.calculate_size(getattr(band, 'margin_top', 0))
            band_height += self.calculate_size(getattr(band, 'margin_bottom', 0))

            self.update_top_pos(band_height)

        # Updates left position
        if getattr(band, 'display_inline', False):
            self.update_left_pos(band.width + self.calculate_size(getattr(band, 'margin_right', 0)))
        else:
            self.update_left_pos(set=0)

        # Child bands
        for child_band in band.child_bands or []: # TODO This "or []" here is a quickfix
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
                top_position=self.calculate_size(self.report.margin_top),
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
                top_position=self.calculate_size(self.report.page_size[1]) -\
                    self.calculate_size(self.report.margin_bottom) -\
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
        return calculate_size(size)

    def get_left_pos(self):
        """Returns the left position of the drawer. Is useful on inline displayed detail bands"""
        return self.calculate_size(self.report.margin_left) + self._current_left_position

    def get_available_width(self):
        return self.calculate_size(self.report.page_size[0]) - self.calculate_size(self.report.margin_left) -\
                self.calculate_size(self.report.margin_right) - self._current_left_position

    def calculate_top(self, *args):
        return sum(args)

    def get_top_pos(self):
        """We use this to use this to get the current top position, 
        considering also the top margin."""
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

    def make_paragraph(self, text, style=None):
        """Uses the Paragraph class to return a new paragraph object"""
        raise Exception('Not implemented')

    def wrap_paragraph_on(self, paragraph, width, height):
        """Wraps the paragraph on the height/width informed"""
        raise Exception('Not implemented')

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
        self._groups_working_values = self._groups_values.copy()

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

        # Update working values for groups
        self._groups_working_values = self._groups_values

        # Loops on groups to render changed ones
        for group in self.report.groups:
            if self._groups_changed.get(group, None) and\
               group.band_header and\
               group.band_header.visible:
                self.force_blank_page_by_height(self.calculate_size(group.band_header.height))
                self.render_band(group.band_header)

    def render_groups_footers(self, force=False):
        """Renders the report footers using previous 'changed' definition calculated by
        'calc_changed_groups'"""

        # Loops on groups to render changed ones
        for group in reversed(self.report.groups):
            if force or ( self._groups_changed.get(group, None) and\
                          self._groups_stack and\
                          self._groups_stack[-1] == group ):
                if group.band_footer and group.band_footer.visible:
                    self.force_blank_page_by_height(self.calculate_size(group.band_footer.height))
                    self.render_band(group.band_footer)

                if self._groups_stack:
                    self._groups_working_values.pop(self._groups_stack[-1])

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

        filter_dict = dict([(group.attribute_name, value) for group, value in self._groups_working_values.items()])

        def filter_object(obj):
            for k,v in filter_dict.items():
                if get_attr_value(obj, k) != v:
                    return False

            return obj

        return filter(filter_object, self.report.queryset)

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
            if not subreport.band_detail or not subreport.visible:
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
                    if subreport.band_header.visible:
                        self.render_band(subreport.band_header)

                # Forces new page if there is no available space
                force_new_page(subreport.band_detail.height)

                # Renders the detail band
                if subreport.band_detail.visible:
                    self.render_band(subreport.band_detail, current_object=obj)

            # Renders the footer band
            if subreport.band_footer:
                # Forces new page if there is no available space
                force_new_page(subreport.band_footer.height)

                # Renders the header band
                if subreport.band_footer.visible:
                    self.render_band(subreport.band_footer)

            # Sets back the default currenty queryset
            self._current_queryset = None

    def make_paragraph_style(self, band, style=None):
        """Merge report default_style + band default_style + widget style"""
        raise Exception('Not implemented')

    def keep_in_frame(self, widget, width, height, paragraphs, mode):
        raise Exception('Not implemented')

