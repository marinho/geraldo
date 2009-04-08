import datetime
from base import ReportGenerator

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.units import cm

from geraldo.base import get_attr_value
from geraldo.widgets import Widget, Label, SystemField
from geraldo.graphics import Graphic, RoundRect, Rect, Line, Circle, Arc,\
        Ellipse, Image

class ReportPage(object):
    rect = None
    elements = None
    width = None

    def __init__(self):
        self.elements = []

class PDFGenerator(ReportGenerator):
    """This is a generator to output a PDF using ReportLab library with
    preference by its Platypus API"""
    filename = None

    _is_first_page = True
    _is_latest_page = True
    _current_top_position = 0
    _current_left_position = 0
    _current_page_number = 0
    _current_object = None
    _generation_datetime = None

    # Groupping
    _groups_values = None
    _groups_previous_values = None
    _groups_values = None
    _groups_changed = None
    _groups_stack = None

    # The rendered report have pages, each page is a ReportPage instance
    _rendered_pages = None
    _page_rect = None

    def __init__(self, report, filename):
        super(PDFGenerator, self).__init__(report)

        self._rendered_pages = []
        self.filename = filename
        self._groups_values = {}
        self._groups_previous_values = {}
        self._groups_changed = {}
        self._groups_stack = []

    def execute(self):
        """Generates a PDF file using ReportLab pdfgen package."""

        # Initializes pages
        self._is_first_page = True

        # Initializes the temporary PDF canvas (just to be used as reference)
        self.canvas = Canvas(self.filename, pagesize=self.report.page_size)

        # Render pages
        self.render_bands()

        # Initializes the definitive PDF canvas
        self.start_pdf(self.filename)

        self.generate_pages()

        # Finalizes the canvas
        self.canvas.save()

    def start_pdf(self, filename):
        """Initializes the PDF document with some properties and methods"""
        # Sets the PDF canvas
        self.canvas = Canvas(filename=filename, pagesize=self.report.page_size)

        # Set PDF properties
        self.canvas.setTitle(self.report.title)
        self.canvas.setAuthor(self.report.author)

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
                'right': left_position + band.width, #self.report.page_size[0] - self.report.margin_right,
                'bottom': top_position - band.height,
                'height': band.height,
                }
        return band_rect

    def render_band(self, band, top_position=None, left_position=None,
            update_top=True, current_object=None):
        """Generate a band having the current top position or informed as its
        top coordinate"""
        current_object = current_object or self._current_object

        # Page width. This should be done in a metaclass in Report domain TODO
        self._rendered_pages[-1].width = self.report.page_size[0] -\
                self.report.margin_left - self.report.margin_right

        # Default value for band width
        band.width = band.width or self._rendered_pages[-1].width

        # Coordinates
        left_position = left_position or self.get_left_pos()

        if left_position > self.report.margin_left and\
           getattr(band, 'display_inline', False) and\
           band.width < self.get_available_width():
            self.update_top_pos(decrease=band.height)
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
                widget.report = self.report # This should be done by a metaclass in Band domain TODO
                widget.band = band # This should be done by a metaclass in Band domain TODO
                widget.page = self._rendered_pages[-1]

                if isinstance(widget, SystemField):
                    widget.left = band_rect['left'] + widget.left
                    widget.top = temp_top - widget.top
                elif isinstance(widget, Label):
                    widget.para = Paragraph(widget.text, self.make_paragraph_style(band, widget.style))
                    widget.para.wrapOn(self.canvas, widget.width, widget.height)
                    widget.left = band_rect['left'] + widget.left
                    widget.top = temp_top - widget.top - widget.para.height

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
                    graphic.left = band_rect['left'] + graphic.left
                    graphic.top = top_position - graphic.top - graphic.height
                elif isinstance(graphic, Rect):
                    graphic.left = band_rect['left'] + graphic.left
                    graphic.top = top_position - graphic.top - graphic.height
                elif isinstance(graphic, Line):
                    graphic.left = band_rect['left'] + graphic.left
                    graphic.top = top_position - graphic.top
                    graphic.right = band_rect['left'] + graphic.right
                    graphic.bottom = top_position - graphic.bottom
                elif isinstance(graphic, Circle):
                    graphic.left_center = band_rect['left'] + graphic.left_center
                    graphic.top_center = top_position - graphic.top_center
                elif isinstance(graphic, Arc):
                    graphic.left = band_rect['left'] + graphic.left
                    graphic.top = top_position - graphic.top
                    graphic.right = band_rect['left'] + graphic.right
                    graphic.bottom = top_position - graphic.bottom
                elif isinstance(graphic, Ellipse):
                    graphic.left = band_rect['left'] + graphic.left
                    graphic.top = top_position - graphic.top
                    graphic.right = band_rect['left'] + graphic.right
                    graphic.bottom = top_position - graphic.bottom
                elif isinstance(graphic, Image):
                    graphic.left = band_rect['left'] + graphic.left
                    graphic.top = top_position - graphic.top - graphic.height

                self._rendered_pages[-1].elements.append(graphic)

        # Updates top position
        if update_top:
            self.update_top_pos(band.height + getattr(band, 'margin_top', 0))

        # Updates left position
        if getattr(band, 'display_inline', False):
            self.update_left_pos(band.width + getattr(band, 'margin_right', 0))
        else:
            self.update_left_pos(set=0)

        # Child bands
        for child_band in band.child_bands or []: # XXX This "or []" here is a quickfix
            # Doesn't generate if it is not visible
            if not child_band.visible:
                continue

            self.force_blank_page_by_height(child_band.height)

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
        self.force_blank_page_by_height(self.report.band_summary.height)

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
                top_position=self.report.page_size[1] - self.report.margin_top,
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
                top_position=self.report.margin_bottom + self.report.band_page_footer.height,
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

    def generate_pages(self):
        self._generation_datetime = datetime.datetime.now()

        for num, page in enumerate([page for page in self._rendered_pages if page.elements]):
            self._current_page_number = num

            # Loop at band widgets
            for element in page.elements:
                # Widget element
                if isinstance(element, Widget):
                    widget = element
    
                    # Set element colors
                    self.set_fill_color(widget.font_color)
    
                    self.generate_widget(widget, self.canvas, num)
    
                # Graphic element
                elif isinstance(element, Graphic):
                    graphic = element
    
                    # Set element colors
                    self.set_fill_color(graphic.fill_color)
                    self.set_stroke_color(graphic.stroke_color)
                    self.set_stroke_width(graphic.stroke_width)
    
                    self.generate_graphic(graphic, self.canvas)

            self.canvas.showPage()
 
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
                if self.get_available_height() < d_band.height:
                    # right margin is not considered to calculate the necessary space
                    d_width = d_band.width + getattr(d_band, 'margin_left', 0)

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
                self._page_rect['top'] = self.report.page_size[1] - self._page_rect['top']
                self._page_rect['bottom'] = self.report.page_size[1] - self._page_rect['bottom']

            self.render_border(self.report.borders, self._page_rect)

    def get_left_pos(self):
        """Returns the left position of the drawer. Is useful on inline displayed detail bands"""
        return self.report.margin_left + self._current_left_position

    def get_available_width(self):
        return self.report.page_size[0] - self.report.margin_left - self.report.margin_right -\
                self._current_left_position

    def get_top_pos(self):
        """Since the coordinates are bottom-left on PDF, we have to use this to get
        the current top position, considering also the top margin."""
        ret = self.report.page_size[1] - self.report.margin_top - self._current_top_position

        if self.report.band_page_header:
            ret -= self.report.band_page_header.height

        return ret

    def get_available_height(self):
        """Returns the available client height area from the current top position
        until the end of page, considering the bottom margin."""
        ret = self.report.page_size[1] - self.report.margin_bottom -\
                self.report.margin_top - self._current_top_position

        if self.report.band_page_header:
            ret -= self.report.band_page_header.height

        if self.report.band_page_footer:
            ret -= self.report.band_page_footer.height

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

    def get_page_count(self): # TODO
        """Calculate and returns the page count for this report. The challenge
        here is do this calculate before to generate the pages."""
        return len(self._rendered_pages)

    # Stylizing

    def set_fill_color(self, color):
        """Sets the current fill on canvas. Used for fonts and shape fills"""
        self.canvas.setFillColor(color)
    
    def set_stroke_color(self, color):
        """Sets the current stroke on canvas"""
        self.canvas.setStrokeColor(color)

    def set_stroke_width(self, width):
        """Sets the stroke/line width for shapes"""
        self.canvas.setLineWidth(width)

    # Groups topic

    def calc_changed_groups(self, force_no_changed=False):
        """Render reports groups - only group headers for a while"""
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
                self.force_blank_page_by_height(group.band_header.height)
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
                    self.force_blank_page_by_height(group.band_footer.height)
                    self.render_band(group.band_footer)

                self._groups_stack.pop()

    def get_objects_in_group(self):
        """Return objects filtered in the current group or all if there is no
        group"""
        if not self._groups_stack:
            return self.report.queryset

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
        for subreport in self.report.subreports:
            # Subreports must have detail band
            if not subreport.detail_band:
                continue

            # Sets the parent object and automatically clear the queryset
            # in memory
            subreport.parent_object = self._current_object

            # Loops objects
            for obj in subreport.get_objects_list():
                # Forces new page if there is no available space
                if self.get_available_height() < subreport.detail_band.height:
                    self.render_page_footer()
                    self.force_new_page(insert_new_page=False)

                # Renders the detail band
                self.render_band(subreport.detail_band, current_object=obj)

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

        return ParagraphStyle(name=datetime.datetime.now().strftime('%H%m%s'), **d_style)

    def generate_widget(self, widget, canvas=None, page_number=0):
        """Renders a widget element on canvas"""
        if isinstance(widget, SystemField):
            # Sets system fields
            widget.fields['report_title'] = self.report.title
            widget.fields['page_number'] = page_number + 1
            widget.fields['page_count'] = self.get_page_count()
            widget.fields['current_datetime'] = self._generation_datetime
            widget.fields['report_author'] = self.report.author

            para = Paragraph(widget.text, self.make_paragraph_style(widget.band, widget.style))
            para.wrapOn(canvas, widget.width, widget.height)
            para.drawOn(canvas, widget.left, widget.top - para.height)
        elif isinstance(widget, Label):
            widget.para.drawOn(canvas, widget.left, widget.top)

    def generate_graphic(self, graphic, canvas=None):
        """Renders a graphic element"""
        canvas = canvas or self.canvas

        if isinstance(graphic, RoundRect):
            canvas.roundRect(
                    graphic.left,
                    graphic.top,
                    graphic.width,
                    graphic.height,
                    graphic.radius,
                    graphic.stroke,
                    graphic.fill,
                    )
        elif isinstance(graphic, Rect):
            canvas.rect(
                    graphic.left,
                    graphic.top,
                    graphic.width,
                    graphic.height,
                    graphic.stroke,
                    graphic.fill,
                    )
        elif isinstance(graphic, Line):
            canvas.line(
                    graphic.left,
                    graphic.top,
                    graphic.right,
                    graphic.bottom,
                    )
        elif isinstance(graphic, Circle):
            canvas.circle(
                    graphic.left_center,
                    graphic.top_center,
                    graphic.radius,
                    graphic.stroke,
                    graphic.fill,
                    )
        elif isinstance(graphic, Arc):
            canvas.arc(
                    graphic.left,
                    graphic.top,
                    graphic.right,
                    graphic.bottom,
                    graphic.start_angle,
                    graphic.extent,
                    )
        elif isinstance(graphic, Ellipse):
            canvas.ellipse(
                    graphic.left,
                    graphic.top,
                    graphic.right,
                    graphic.bottom,
                    graphic.stroke,
                    graphic.fill,
                    )
        elif isinstance(graphic, Image) and graphic.image:
            canvas.drawInlineImage(
                    graphic.image,
                    graphic.left,
                    graphic.top,
                    graphic.width,
                    graphic.height,
                    )

