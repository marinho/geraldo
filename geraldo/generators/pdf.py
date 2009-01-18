from base import ReportGenerator

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.units import cm

from geraldo.widgets import Widget, Label
from geraldo.graphics import Graphic, RoundRect, Rect, Line, Circle, Arc,\
        Ellipse, Image

class PDFGenerator(ReportGenerator):
    """This is a generator to output a PDF using ReportLab library with
    preference by its Platypus API"""
    filename = None

    _is_first_page = True
    _is_latest_page = True
    _current_top_position = 0
    _current_page_number = 0
    _current_object = None

    def __init__(self, report, filename):
        super(PDFGenerator, self).__init__(report)

        self.filename = filename

    def execute(self):
        """Generate a PDF file using ReportLab pdfgen package."""

        # Initializes the PDF canvas
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

        self._is_first_page = True

    def generate_band(self, band, top_position=None):
        """Generate a band having the current top position or informed as its
        top coordinate"""

        # Coordinates and dimensions
        temp_top = top_position = top_position or self.get_top_pos()
        band_rect = {
                'left': self.report.margin_left,
                'top': top_position,
                'right': self.report.page_size[0] - self.report.margin_right,
                'bottom': top_position - band.height,
                }
        # This should be done by a metaclass in Report domain TODO
        band.width = self.report.page_size[0] - self.report.margin_left - self.report.margin_right

        # Loop at band widgets
        for element in band.elements:
            # Widget element
            if isinstance(element, Widget):
                widget = element

                # Set element colors
                self.set_fill_color(self.report.default_font_color)

                # Set widget basic attributes
                widget.instance = self._current_object
                widget.generator = self
                widget.report = self.report # This should be done by a metaclass in Band domain TODO
                widget.band = band # This should be done by a metaclass in Band domain TODO

                if isinstance(widget, Label):
                    para = Paragraph(widget.text, ParagraphStyle(name='Normal', **widget.style))
                    para.wrapOn(self.canvas, widget.width, widget.height)
                    para.drawOn(self.canvas, self.report.margin_left + widget.left, temp_top - widget.top - para.height)

            # Graphic element
            elif isinstance(element, Graphic):
                graphic = element

                # Set element colors
                self.set_fill_color(graphic.fill_color or self.report.default_fill_color)
                self.set_stroke_color(graphic.stroke_color or self.report.default_stroke_color)
                self.set_stroke_width(graphic.stroke_width)

                if isinstance(element, RoundRect):
                    self.canvas.roundRect(
                            self.report.margin_left + graphic.left,
                            top_position - graphic.top - graphic.height,
                            graphic.width,
                            graphic.height,
                            graphic.radius,
                            graphic.stroke,
                            graphic.fill,
                            )
                elif isinstance(element, Rect):
                    self.canvas.rect(
                            self.report.margin_left + graphic.left,
                            top_position - graphic.top - graphic.height,
                            graphic.width,
                            graphic.height,
                            graphic.stroke,
                            graphic.fill,
                            )
                elif isinstance(element, Line):
                    self.canvas.line(
                            self.report.margin_left + graphic.left,
                            top_position - graphic.top,
                            self.report.margin_left + graphic.right,
                            top_position - graphic.bottom,
                            )
                elif isinstance(element, Circle):
                    self.canvas.circle(
                            self.report.margin_left + graphic.left_center,
                            top_position - graphic.top_center,
                            graphic.radius,
                            graphic.stroke,
                            graphic.fill,
                            )
                elif isinstance(element, Arc):
                    self.canvas.arc(
                            self.report.margin_left + graphic.left,
                            top_position - graphic.top,
                            self.report.margin_left + graphic.right,
                            top_position - graphic.bottom,
                            graphic.start_angle,
                            graphic.extent,
                            )
                elif isinstance(element, Ellipse):
                    self.canvas.ellipse(
                            self.report.margin_left + graphic.left,
                            top_position - graphic.top,
                            self.report.margin_left + graphic.right,
                            top_position - graphic.bottom,
                            graphic.stroke,
                            graphic.fill,
                            )
                elif isinstance(element, Image):
                    self.canvas.drawInlineImage(
                            graphic.image,
                            self.report.margin_left + graphic.left,
                            top_position - graphic.top - graphic.height,
                            graphic.width,
                            graphic.height,
                            )

        # Band borders
        if band.borders.get('all', None):
            self.canvas.rect(
                    band_rect['left'],
                    band_rect['top'] - band.height,
                    band_rect['right'] - band_rect['left'],
                    band.height,
                    )

        if band.borders.get('top', None):
            self.canvas.line(band_rect['left'], band_rect['top'], band_rect['right'],
                    band_rect['top'])

        if band.borders.get('right', None):
            self.canvas.line(band_rect['right'], band_rect['top'], band_rect['right'],
                    band_rect['bottom'])

        if band.borders.get('bottom', None):
            self.canvas.line(band_rect['left'], band_rect['bottom'], band_rect['right'],
                    band_rect['bottom'])

        if band.borders.get('left', None):
            self.canvas.line(band_rect['left'], band_rect['top'], band_rect['left'],
                    band_rect['bottom'])

    def generate_begin(self):
        """Generate the report begin band if it exists"""
        if not self.report.band_begin:
            return

        # Call method that print the band area and its widgets
        self.generate_band(self.report.band_begin)
        
        # Update top position after this band
        self.update_top_pos(self.report.band_begin.height)

    def generate_summary(self):
        """Generate the report summary band if it exists"""
        if not self.report.band_summary:
            return

        # Check to force new page if there is no available space
        force_new_page = self.get_available_height() < self.report.band_summary.height

        if force_new_page:
            # Ends the current page
            self._current_top_position = 0
            self.canvas.showPage()

            # Starts a new one
            self.start_new_page()

        # Call method that print the band area and its widgets
        self.generate_band(self.report.band_summary)

        if force_new_page:
            self.generate_page_footer()

    def generate_page_header(self):
        """Generate the report page header band if it exists"""
        if not self.report.band_page_header:
            return

        # Call method that print the band area and its widgets
        self.generate_band(
                self.report.band_page_header,
                self.report.page_size[1] - self.report.margin_top
                )

    def generate_page_footer(self):
        """Generate the report page footer band if it exists"""
        if not self.report.band_page_footer:
            return

        # Call method that print the band area and its widgets
        self.generate_band(
                self.report.band_page_footer,
                self.report.margin_bottom + self.report.band_page_footer.height,
                )

    def generate_pages(self):
        """Loops into the queryset to create the report pages until the end"""
        # Preparing local auxiliar variables
        self._current_page_number = 0
        self._current_object_index = 0
        objects = self.report.queryset and \
                  [object for object in self.report.queryset] or\
                  []

        # Empty report
        if self.report.print_if_empty and not objects:
            self.start_new_page()
            self.generate_begin()
            self.end_current_page()

        # Loop for pages
        while self._current_object_index < len(objects):
            # Starts a new page and generates the page header band
            self.start_new_page()

            # Generate the report begin band
            if self._current_page_number == 0:
                self.generate_begin()

            # Does generate objects if there is no details band
            if not self.report.band_detail:
                self._current_object_index = len(objects)

            # Loop for objects to go into grid on current page
            while self._current_object_index < len(objects):
                # Get current object from list
                self._current_object = objects[self._current_object_index]

                # Generates the detail band
                self.generate_band(self.report.band_detail)

                # Updates top position
                self.update_top_pos(self.report.band_detail.height)

                # Next object
                self._current_object_index += 1

                # Break is this is the end of this page
                if self.get_available_height() < self.report.band_detail.height:
                    break

            # Sets this is the latest page or not
            self._is_latest_page = self._current_object_index >= len(objects)

            # Ends the current page, printing footer and summary and necessary
            self.end_current_page()

            # Breaks if this is the latest item
            if self._is_latest_page:
                break

            # Increment page number
            self._current_page_number += 1

    def start_new_page(self, with_header=True):
        """Do everything necessary to be done to start a new page"""
        if with_header:
            self.generate_page_header()

    def end_current_page(self):
        """Closes the current page, using showPage method. Everything done after
        this will draw into a new page. Before this, using the generate_page_footer
        method to draw the footer"""
        self.generate_page_footer()

        if self._is_latest_page:
            self.generate_summary()

        self.canvas.showPage()

        self._current_page_number += 1
        self._is_first_page = False
        self.update_top_pos(set=0) # <---- update top position

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

    def get_page_count(self): # TODO
        """Calculate and returns the page count for this report. The challenge
        here is do this calculate before to generate the pages."""
        pass

    def set_fill_color(self, color):
        """Sets the current fill on canvas. Used for fonts and shape fills"""
        self.canvas.setFillColor(color)
    
    def set_stroke_color(self, color):
        """Sets the current stroke on canvas"""
        self.canvas.setStrokeColor(color)

    def set_stroke_width(self, width):
        """Sets the stroke/line width for shapes"""
        self.canvas.setLineWidth(width)

